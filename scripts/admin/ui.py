"""ui — обёртки над questionary под нужды пайплайнов.

Все интерактивные виджеты собраны здесь, чтобы пайплайны не зависели
от questionary напрямую. Если решим заменить либу или вообще выпилить
интерактив, правится только этот файл.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

import questionary
from questionary import Choice

T = TypeVar("T")

CREATE_NEW = object()
"""Sentinel-значение, которое возвращает ``select_or_create`` при выборе
варианта Создать новый."""


def select_or_create(
    title: str,
    items: list[T],
    display: Callable[[T], str],
    create_label: str = "+ Создать нового",
) -> T | object:
    """Показывает список с навигацией стрелками и пунктом Создать новый.

    Возвращает выбранный элемент или sentinel ``CREATE_NEW``, если юзер
    выбрал Создать новый.

    Аргументы:
        title: Заголовок над списком.
        items: Объекты для выбора.
        display: Функция, превращающая объект в строку для отображения.
        create_label: Текст последнего пункта Создать новый.
    """
    choices: list[Choice] = [Choice(display(item), value=item) for item in items]
    choices.append(Choice(create_label, value=CREATE_NEW))
    answer = questionary.select(title, choices=choices, use_shortcuts=False).ask()
    if answer is None:
        raise SystemExit(1)
    return answer


def ask_text(
    prompt: str,
    *,
    default: str = "",
    validate: Callable[[str], bool | str] | None = None,
) -> str:
    """Запрашивает текстовое поле с опциональной валидацией.

    Аргументы:
        prompt: Подпись поля.
        default: Значение по умолчанию.
        validate: Возвращает True или строку с ошибкой.
    """
    answer = questionary.text(prompt, default=default, validate=validate).ask()
    if answer is None:
        raise SystemExit(1)
    return answer


def heading(text: str) -> None:
    """Печатает шапку шага."""
    print()
    print(f">> {text}")


def kv(key: str, value: str) -> None:
    """Печатает строку формата ``key: value`` с выравниванием."""
    print(f"  {key:<12}{value}")
