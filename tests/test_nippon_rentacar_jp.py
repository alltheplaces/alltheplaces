from locations.items import Feature
from locations.spiders.nippon_rentacar_jp import NipponRentacarJPSpider


def hours(data: dict) -> str | None:
    (item,) = NipponRentacarJPSpider().post_process_item(Feature(), data, None)
    return item["opening_hours"].as_opening_hours() if item.get("opening_hours") else None


def test_daily_hours():
    data = {f"eigyo_{d}": "08:00～20:00" for d in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]}
    assert hours(data) == "Mo-Su 08:00-20:00"


def test_closed_day_and_single_digit_hour():
    data = {f"eigyo_{d}": "8:00～19:00" for d in ["mon", "tue", "wed", "thu", "fri", "sat"]}
    data["eigyo_sun"] = "休業"
    assert hours(data) == "Mo-Sa 08:00-19:00; Su closed"


def test_unparseable_text_is_skipped():
    assert hours({"eigyo_mon": "※各曜日の営業時間に準じます。"}) is None
