from locations.spiders.copain_sakura_jp import CopainSakuraJPSpider


def hours(lines: list[str]) -> str | None:
    oh = CopainSakuraJPSpider().parse_hours(lines)
    return oh.as_opening_hours() if oh else None


def test_weekday_and_weekend():
    assert hours(["平日　9：00～18：00", "土・日・祝日　9：00～17：00", "※12/31～1/3を除く"]) == (
        "Mo-Fr 09:00-18:00; Sa-Su 09:00-17:00"
    )


def test_day_per_line_with_closed_days_and_spaced_holiday():
    lines = [
        "月曜日　　 定休日",
        "火曜日　10:00～18:00",
        "水曜日　10:00～18:00",
        "木曜日　10:00～18:00",
        "金曜日　10:00～18:00",
        "土曜日　10:00～18:00",
        "日曜日　　 定休日",
        "祝　日　10:00～18:00",
    ]
    assert hours(lines) == "Tu-Sa 10:00-18:00"


def test_day_ranges_and_sunday_note():
    assert hours(["火曜～土曜　10：00～17：00", "祝日　　10：00～17：00"]) == "Tu-Sa 10:00-17:00"
    assert hours(["月～土曜日・祝日　9：00～18：00", "※日曜日はお休み", "※12/31～1/3除く"]) == "Mo-Sa 09:00-18:00"


def test_unclear_hours_are_skipped():
    assert hours(["9：00～18：00", "※12/31～1/3を除く"]) is None
    assert hours(["平日9：30～18：30（13：00～14：00除く）", "学校休業日9：30～18：30"]) is None
    assert hours(["平日9：30～18：30（13：00～14：00除く）"]) is None
    assert hours(["平日9：30～18：30", "（13：00～14：00除く）"]) is None
    assert hours(["平日9：30～18：30", "※13：00～14：00は休憩"]) is None
    assert hours(["平日　9：00～18：00", "土・日・祝日　9：00～18：00", "※第一日曜日のみ営業"]) is None
    assert hours([]) is None
