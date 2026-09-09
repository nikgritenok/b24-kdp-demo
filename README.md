# b24-kdp-demo

Демо-прототип: выгрузка задач из Битрикс24 (REST, входящий вебхук) → сводный отчёт по статусам и загрузке сотрудников (pandas) → summary.txt + report.xlsx.

## Запуск
```bash
pip install requests pandas openpyxl
export B24_WEBHOOK="https://XXX.bitrix24.ru/rest/1/КОД/"
python3 b24_demo.py
```

Показывает: REST API Битрикс24, вебхуки, автопостраничение, нормализацию данных, pandas groupby/agg, экспорт в Excel.
