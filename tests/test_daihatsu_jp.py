from locations.spiders.daihatsu_jp import DaihatsuJPSpider


def hours(text: str, closed: str) -> str | None:
    oh = DaihatsuJPSpider.parse_hours(text, closed)
    return oh.as_opening_hours() if oh else None


def test_weekly_closing_day():
    assert hours("9:30〜18:00", "毎週月曜日") == "Tu-Su 09:30-18:00"


def test_two_closing_days_written_together():
    assert hours("9:30〜18:00", "毎週月・火曜日定休") == "We-Su 09:30-18:00"
    assert hours("9:30〜18:00", "毎週月曜日・火曜日") == "We-Su 09:30-18:00"


def test_closing_day_range():
    assert hours("10:00〜18:00", "毎週月〜水曜日") == "Th-Su 10:00-18:00"
    assert hours("10:00〜18:00", "毎週月曜日～水曜日") == "Th-Su 10:00-18:00"


def test_full_width_japanese_times():
    assert hours("１０時〜１８時３０分", "毎週水曜日") == "Mo-Tu 10:00-18:30; Th-Su 10:00-18:30"
    assert hours("午前10:00〜午後6:00", "年中無休") == "Mo-Su 10:00-18:00"


def test_workshop_intake_note_is_ignored():
    assert hours("9:30〜18:00(サービス受付17:30まで)", "毎週火曜日") == "Mo 09:30-18:00; We-Su 09:30-18:00"


def test_yearly_holidays_are_ignored():
    closed = "毎週月曜日(年末年始・GW・お盆のお休みにつきましては店舗までお問い合わせください)"
    assert hours("10:00〜18:00", closed) == "Tu-Su 10:00-18:00"


def test_unclear_cases_are_skipped():
    assert hours("月〜金9:30−18:00/土・日9:00−18:00", "毎週水曜日") is None
    assert hours("9:30〜18:00", "毎週火曜日、毎月第1・第3月曜日") is None
    assert hours("9:30〜18:00", "毎週火曜日(第2月曜定休日)") is None
    assert hours("9:30〜18:00", "火曜日・一部水曜日") is None
    assert hours("9:30〜18:00", "詳細は【営業カレンダー】をご覧ください。") is None
    assert hours("9:30〜18:00", "月曜・火曜・会社指定休日") is None
