1. ensure that report_card_subjects isn't fetched twice, like date_sheet_subjects

```py
read_report_card = ReportCardReadDetail.model_validate(report_card)
```

2. automated migrations using alembic
3. populate old students data
