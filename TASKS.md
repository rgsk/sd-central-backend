- ensure that report_card_subjects isn't fetched twice, like date_sheet_subjects

```py
read_report_card = ReportCardReadDetail.model_validate(report_card)
```

- automated migrations using alembic
- populate old students data
