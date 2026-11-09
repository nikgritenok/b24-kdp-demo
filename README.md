# b24-kdp-demo: task summary from Bitrix24

One command, one report for the person who runs the team.

The script takes a Bitrix24 incoming webhook, pulls every task through the REST API with automatic pagination, and builds the summaries a manager actually asks for: how many tasks per person, who is overloaded, what is overdue. Output is `summary.txt` plus `report.xlsx` with two sheets. If a Telegram bot token is set, the short version arrives in chat.

## Why

A manager who wants to know the real state of the work either walks through Bitrix24 by hand for half an hour or asks people. Both give answers that are already stale by the time they arrive.

## Who it is for

- Planning a week and spreading load: see who has what before assigning more.
- Deadline pressure: see the share of overdue tasks and whose name is on them.
- Reporting upward: answer with numbers in a minute instead of collecting them for a day.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # B24_WEBHOOK, optional TG token and chat id
python main.py
```

## Output

- `summary.txt`: short text summary
- `report.xlsx`: sheets "Задачи" and "Загрузка сотрудников"
- Telegram message, if a bot is configured

## What it shows

Bitrix24 REST through an incoming webhook, pagination and API error handling, pandas aggregation, Excel export with openpyxl, optional Telegram delivery. The whole thing is one file, `main.py`, because the point was a tool that runs before lunch, not a framework.

## License

MIT, see [LICENSE](LICENSE).
