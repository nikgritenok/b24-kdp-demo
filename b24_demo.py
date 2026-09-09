# -*- coding: utf-8 -*-
"""
Демо-скрипт для собеседования: выгрузка задач из Битрикс24 -> сводный отчёт.
Показывает ровно то, что просят в вакансии: REST API, вебхуки, pandas, отчёт по загрузке.

Использование:
  1. В своём (бесплатном) Битрикс24: Разработчик -> Другое -> Входящий вебхук
     с правами task, user. Скопируешь URL вида https://XXX.bitrix24.ru/rest/1/xxxxxxxx/
  2. export B24_WEBHOOK="https://XXX.bitrix24.ru/rest/1/xxxxxxxx/"
  3. python b24_demo.py   (поставь: pip install requests pandas openpyxl)

Получишь:
  - summary.txt  — сводка по проектам и загрузке сотрудников
  - report.xlsx  — те же данные листами (можно показать на экране)
"""

import os
import sys
from collections import defaultdict
from datetime import datetime

import requests
import pandas as pd

WEBHOOK = os.environ.get("B24_WEBHOOK", "")
if not WEBHOOK:
    sys.exit("Задай переменную B24_WEBHOOK (URL входящего вебхука Битрикс24)")
if not WEBHOOK.endswith("/"):
    WEBHOOK += "/"


def call(method: str, params: dict | None = None) -> list[dict]:
    """Вызов метода REST API Битрикс24 с автопостраничением."""
    items, start = [], 0
    while True:
        r = requests.post(f"{WEBHOOK}{method}", json={**(params or {}), "start": start}, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"{method}: {data['error']} — {data.get('error_description')}")
        batch = data.get("result", [])
        if isinstance(batch, dict):
            batch = batch.get("tasks", [])
        # Битрикс24 может отдавать ключи в camelCase (responsibleId) —
        # приводим к классическому UPPER_SNAKE, уже-UPPER ключи не трогаем
        import re
        def norm(k):
            return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', k).upper()
        items.extend({norm(k): v for k, v in t.items()} for t in batch)
        if not data.get("next"):
            return items
        start = data["next"]


def main():
    # 1. Выгружаем задачи и пользователей
    tasks = call("tasks.task.list", params={})
    users = call("user.get")
    uname = {u["ID"]: f"{u.get('NAME', '')} {u.get('LAST_NAME', '')}".strip() for u in users}

    df = pd.DataFrame(tasks)
    if df.empty:
        sys.exit("В портале нет задач — создайте 3-5 тестовых задач в Битрикс24 перед запуском")

    # 2. Очистка и трансформация «сырых» данных
    df["responsible"] = df["RESPONSIBLE_ID"].astype(str).map(
        {str(k): v for k, v in uname.items()})
    df["deadline"] = pd.to_datetime(df["DEADLINE"], errors="coerce", utc=True).dt.tz_localize(None)
    df["created"] = pd.to_datetime(df["CREATED_DATE"], errors="coerce", utc=True).dt.tz_localize(None)
    df["status_num"] = pd.to_numeric(df["STATUS"], errors="coerce")
    df["overdue"] = (df["deadline"].notna()) & (df["deadline"] < pd.Timestamp.now()) & (df["status_num"] != 5)
    status_map = {1: "Новая", 2: "Ждёт выполнения", 3: "В работе", 4: "Ожидает контроля", 5: "Завершена"}
    df["status"] = df["status_num"].map(status_map).fillna("Прочее")
    df["hours_est"] = pd.to_numeric(df["TIME_ESTIMATE"], errors="coerce").fillna(0) / 3600

    # 3. Сводки — то, что в вакансии названо «сводки по проектам, загрузка сотрудников»
    by_status = df.groupby("status").size()
    by_person = (df.groupby("responsible")
                   .agg(задач=("ID", "count"),
                        в_работе=("status", lambda s: (s == "В работе").sum()),
                        просрочено=("overdue", "sum"),
                        часов_оценка=("hours_est", "sum"))
                   .sort_values("задач", ascending=False).astype(int))
    overdue_share = df["overdue"].mean() * 100

    lines = [f"Отчёт по задачам Битрикс24 — {datetime.now():%d.%m.%Y %H:%M}", ""]
    lines.append("Статусы задач:")
    lines.extend(f"  {k}: {v}" for k, v in by_status.items())
    lines.append("")
    lines.append("Загрузка сотрудников:")
    lines.extend(f"  {name}: {row['задач']} задач, {row['в_работе']} в работе, "
                 f"{row['просрочено']} просрочено, ~{row['часов_оценка']:.1f} ч оценки"
                 for name, row in by_person.iterrows())
    lines.append("")
    lines.append(f"Доля просроченных: {overdue_share:.0f}%")
    summary = "\n".join(lines)

    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
    with pd.ExcelWriter("report.xlsx") as xl:
        df[["ID", "TITLE", "status", "responsible", "deadline", "overdue", "hours_est"]].to_excel(xl, sheet_name="Задачи", index=False)
        by_person.to_excel(xl, sheet_name="Загрузка сотрудников")

    print(summary)
    print("\nГотово: summary.txt, report.xlsx")


if __name__ == "__main__":
    main()
