"""Деплой Eralands Notifications на прод-VPS.

Запуск: ``make deploy`` (или ``poetry run python -m scripts.deploy``).

Что делает по шагам:
  1. Читает .env.prod, валидирует обязательные секреты
  2. Спрашивает SSH-хост и домен, если не заданы в .env.prod
  3. Собирает локально docker-образ приложения
  4. Пуллит локально postgres:17-alpine и caddy:2-alpine
  5. Пакует все три образа в один tar.gz через ``docker save | gzip``
  6. На сервере: ставит docker (если нет), создаёт REMOTE_DIR/backups
  7. Копирует tar.gz, compose, Caddyfile, .env.prod на сервер
  8. Если есть таблица alembic_version, делает pg_dump в backups/ и ротирует
  9. Загружает образы на сервере, поднимает compose, накатывает alembic upgrade
 10. Ждёт 200 на https://<DOMAIN>/api/health (до 30 попыток × 5с)
"""

import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_PROD = ROOT / ".env.prod"
COMPOSE_PROD = ROOT / "docker-compose.prod.yml"
CADDYFILE = ROOT / "Caddyfile"
IMAGE_NAME = "eralands-notifications:latest"
DEPENDENCY_IMAGES = ["postgres:17-alpine", "caddy:2-alpine"]
TAR_NAME = "eralands-notifications.tar.gz"

# SSH connection multiplexing: один master-сокет переиспользуется всеми ssh/scp.
_SSH_OPTS = [
    "-o",
    "ControlMaster=auto",
    "-o",
    "ControlPath=/tmp/eralands-deploy-%r@%h:%p",
    "-o",
    "ControlPersist=600",
    "-o",
    "ServerAliveInterval=30",
    "-o",
    "ServerAliveCountMax=10",
    "-o",
    "StrictHostKeyChecking=accept-new",
]

BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def step(msg: str) -> None:
    print(f"\n{BLUE}▶ {msg}{RESET}")


def ok(msg: str) -> None:
    print(f"  {GREEN}✓ {msg}{RESET}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠ {msg}{RESET}")


def fail(msg: str) -> None:
    print(f"  {RED}✗ {msg}{RESET}", file=sys.stderr)


def sh(cmd: list[str], **kwargs) -> None:
    """Локальная команда, без shell, с пробросом stdout/stderr."""
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)


def ssh(
    host_user: str, remote_cmd: str, *, check: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(["ssh", *_SSH_OPTS, host_user, remote_cmd], check=check)


def scp(host_user: str, local: Path | str, remote: str) -> None:
    print(f"  scp {local} -> {host_user}:{remote}")
    subprocess.run(["scp", *_SSH_OPTS, str(local), f"{host_user}:{remote}"], check=True)


def parse_env_file(path: Path) -> dict[str, str]:
    """Минималистичный парсер KEY=VALUE. Игнорирует комментарии и пустые строки.

    Не пытается раскрывать ${VAR} и многострочные значения: для .env.prod это не нужно.
    """
    result: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def preflight() -> dict:
    step("Pre-flight checks")

    if not ENV_PROD.exists():
        fail(f".env.prod не найден ({ENV_PROD})")
        print("  Создай его: cp .env.prod.example .env.prod && $EDITOR .env.prod")
        sys.exit(1)
    ok(".env.prod найден")

    env = parse_env_file(ENV_PROD)

    placeholders = {
        "",
        "change-me",
        "change-me-strong-random-password",
        "change-me-strong-random-key",
    }
    required = [
        "DB__PASSWORD",
        "API__KEY",
        "TELEGRAM__TOKEN",
        "TELEGRAM__WEBHOOK_SECRET",
        "TELEGRAM__WEBHOOK_URL",
    ]
    missing = [k for k in required if env.get(k, "") in placeholders]
    if missing:
        fail("В .env.prod не настроены: " + ", ".join(missing))
        sys.exit(1)
    ok("Обязательные секреты заданы")

    ssh_user = env.get("DEPLOY__SSH_USER") or "root"
    ssh_host = env.get("DEPLOY__SSH_HOST", "")
    domain = env.get("DEPLOY__DOMAIN", "")

    while not ssh_host:
        ssh_host = input("\n  SSH host (IP или hostname): ").strip()
    while not domain:
        domain = input("  Домен (например api.example.com): ").strip()

    host_user = f"{ssh_user}@{ssh_host}"

    step(f"Проверяю SSH до {host_user}")
    result = subprocess.run(["ssh", *_SSH_OPTS, host_user, "echo ok"], check=False)
    if result.returncode != 0:
        fail(f"Не удалось подключиться к {host_user}")
        print(
            "  Проверь, что твой публичный ключ добавлен в authorized_keys на сервере."
        )
        sys.exit(1)
    ok(f"SSH ok ({host_user})")

    return {
        "host_user": host_user,
        "domain": domain,
        "remote_dir": env.get("DEPLOY__REMOTE_DIR") or "/opt/eralands-notifications",
        "backup_retention": int(env.get("DEPLOY__BACKUP_RETENTION") or "5"),
        "db_user": env.get("DB__USER") or "notifications",
        "db_name": env.get("DB__NAME") or "notifications",
    }


def build_image() -> None:
    step(f"Сборка образа {IMAGE_NAME}")
    sh(["docker", "build", "-t", IMAGE_NAME, str(ROOT)])
    ok("Образ собран")


def pull_dependency_images() -> None:
    step("Пулл базовых образов локально")
    for image in DEPENDENCY_IMAGES:
        sh(["docker", "pull", image])
    ok("Базовые образы готовы")


def export_images(tar_path: Path) -> None:
    all_images = [IMAGE_NAME, *DEPENDENCY_IMAGES]
    step(f"Упаковка {len(all_images)} образов в {tar_path.name}")
    with open(tar_path, "wb") as f:
        save = subprocess.Popen(["docker", "save", *all_images], stdout=subprocess.PIPE)
        gzip_proc = subprocess.Popen(["gzip", "-c"], stdin=save.stdout, stdout=f)
        save.stdout.close()  # type: ignore[union-attr]
        gzip_proc.wait()
        save.wait()
        if save.returncode or gzip_proc.returncode:
            fail("Не удалось экспортировать образы")
            sys.exit(1)
    size_mb = tar_path.stat().st_size // 1024 // 1024
    ok(f"Образы упакованы ({size_mb} MB)")


def setup_remote(ctx: dict) -> None:
    step(f"Подготовка сервера {ctx['host_user']}")
    remote = shlex.quote(ctx["remote_dir"])
    ssh(
        ctx["host_user"],
        f"""
set -e
if ! command -v docker >/dev/null 2>&1; then
    echo '>>> Docker не найден, устанавливаю через get.docker.com'
    curl -fsSL https://get.docker.com | sh
fi
docker --version
mkdir -p {remote}/backups
""",
    )
    ok("Docker готов, REMOTE_DIR создан")


def transfer_files(ctx: dict, tar_path: Path) -> None:
    step("Передача файлов на сервер")
    remote = ctx["remote_dir"]
    scp(ctx["host_user"], tar_path, f"{remote}/{TAR_NAME}")
    scp(ctx["host_user"], COMPOSE_PROD, f"{remote}/docker-compose.prod.yml")
    scp(ctx["host_user"], CADDYFILE, f"{remote}/Caddyfile")
    scp(ctx["host_user"], ENV_PROD, f"{remote}/.env.prod")
    ok("Файлы переданы")


def backup_database(ctx: dict) -> None:
    """Снимает pg_dump, если есть alembic_version. Skip на первом деплое."""
    step("Бэкап БД (если есть что бэкапить)")
    remote = shlex.quote(ctx["remote_dir"])
    db_user = shlex.quote(ctx["db_user"])
    db_name = shlex.quote(ctx["db_name"])
    retention = ctx["backup_retention"]
    keep_plus_one = retention + 1

    cmd = f"""
set -e
cd {remote}
COMPOSE='docker compose -f docker-compose.prod.yml --env-file .env.prod'
if ! $COMPOSE ps -q postgres 2>/dev/null | grep -q .; then
    echo '>>> Postgres не запущен, бэкап пропускаю (первый деплой)'
    exit 0
fi
has_table=$($COMPOSE exec -T postgres \\
    psql -U {db_user} -d {db_name} -tAc \\
    "SELECT to_regclass('public.alembic_version') IS NOT NULL" 2>/dev/null \\
    | tr -d '[:space:]' || echo f)
if [ "$has_table" != "t" ]; then
    echo '>>> alembic_version отсутствует, бэкап пропускаю'
    exit 0
fi
ts=$(date +%Y%m%d-%H%M%S)
out="backups/dump-${{ts}}.sql.gz"
echo ">>> Сохраняю $out"
$COMPOSE exec -T postgres pg_dump -U {db_user} {db_name} | gzip > "$out"
echo ">>> Размер: $(du -h "$out" | cut -f1)"
echo ">>> Ротация: оставляю последние {retention}"
ls -1t backups/dump-*.sql.gz 2>/dev/null | tail -n +{keep_plus_one} | xargs -r rm -f
"""
    ssh(ctx["host_user"], cmd)
    ok("Бэкап готов (или пропущен)")


def deploy_remote(ctx: dict) -> None:
    step("Загрузка образов и запуск сервисов")
    remote = shlex.quote(ctx["remote_dir"])
    cmd = f"""
set -e
cd {remote}
COMPOSE='docker compose -f docker-compose.prod.yml --env-file .env.prod'
echo '>>> Загружаю образы из {TAR_NAME}'
docker load < {TAR_NAME}
rm {TAR_NAME}
echo '>>> Поднимаю compose (--wait ждёт healthy)'
$COMPOSE up -d --no-build --wait
echo '>>> Применяю миграции'
$COMPOSE exec -T app alembic upgrade head
echo '>>> Чищу неиспользуемые образы'
docker image prune -f
"""
    ssh(ctx["host_user"], cmd)
    ok("Сервисы запущены, миграции применены")


def health_check(ctx: dict) -> None:
    domain = ctx["domain"]
    url = f"https://{domain}/api/health"
    step(f"Health check {url}")
    max_attempts = 30
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            [
                "curl",
                "-sf",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "-k",
                "--max-time",
                "5",
                url,
            ],
            capture_output=True,
            text=True,
        )
        code = result.stdout.strip()
        if code == "200":
            ok(f"Health check пройден (попытка {attempt})")
            return
        print(f"  [{attempt}/{max_attempts}] HTTP {code or 'error'}, жду 5с")
        time.sleep(5)

    warn("Health check таймаут. Логи docker:")
    remote = shlex.quote(ctx["remote_dir"])
    compose = "docker compose -f docker-compose.prod.yml --env-file .env.prod"
    ssh(
        ctx["host_user"],
        f"cd {remote} && {compose} logs --tail=80",
        check=False,
    )
    fail("Деплой не прошёл health check")
    sys.exit(1)


def close_ssh_master(ctx: dict) -> None:
    subprocess.run(
        ["ssh", "-O", "exit", *_SSH_OPTS, ctx["host_user"]],
        check=False,
        capture_output=True,
    )


def main() -> None:
    print(f"{BOLD}=== Eralands Notifications: Production Deploy ==={RESET}")

    ctx = preflight()

    build_image()
    pull_dependency_images()

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tar_path = Path(tmp) / TAR_NAME
            export_images(tar_path)
            setup_remote(ctx)
            transfer_files(ctx, tar_path)

        backup_database(ctx)
        deploy_remote(ctx)
        health_check(ctx)
    finally:
        close_ssh_master(ctx)

    print(
        f"\n{BOLD}{GREEN}✓ Деплой завершён. Сервис доступен на https://{ctx['domain']}/{RESET}\n"
    )


if __name__ == "__main__":
    main()
