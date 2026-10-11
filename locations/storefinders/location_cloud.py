import re
from collections.abc import AsyncIterator, Iterable
from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

# https://location-cloud.navitime.co.jp/


class LocationCloudSpider(Spider):
    dataset_attributes: dict = {"source": "api"}

    api_endpoint: str
    additional_args: str = ""
    website_formatter: str = ""

    async def start(self) -> AsyncIterator[Request]:
        yield self._get_page(0)

    def _get_page(self, offset: int):
        return Request(
            f"{self.api_endpoint}?datum=wgs84&limit=500{self.additional_args}&offset={offset}",
            meta={"offset": offset},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()  # ty: ignore[unresolved-attribute]

        for location in data["items"]:
            item = Feature()
            if self.website_formatter:
                item["website"] = self.website_formatter.format(location["code"])
            item["ref"] = location["code"]
            item["lat"] = location["coord"]["lat"]
            item["lon"] = location["coord"]["lon"]
            item["addr_full"] = location.get("address_name")
            item["postcode"] = location.get("postal_code")

            if self._has_parse_detail_page_override():
                yield Request(
                    item["website"],
                    callback=self._parse_detail_page,
                    cb_kwargs={"item": item, "source_feature": location},
                )
            else:
                yield from self.post_process_feature(item, location)

        if data["count"]["offset"] + data["count"]["limit"] < data["count"]["total"]:
            yield self._get_page(data["count"]["limit"] + response.meta["offset"])

    def _has_parse_detail_page_override(self) -> bool:
        return type(self).parse_detail_page is not LocationCloudSpider.parse_detail_page

    def _parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        for parsed in self.parse_detail_page(response, item, source_feature):
            yield from self.post_process_feature(parsed, source_feature)

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        """Override with any pre-processing on the item."""
        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        """Override with any pre-processing on the item."""
        yield item


def parse_opening_hours(texts: dict[str, str]) -> str | None:
    """Parse the 営業時間（平日）, 営業時間（土曜） and 営業時間（日祝） detail texts."""
    oh = OpeningHours()
    for label, days in (
        ("営業時間（平日）", DAYS_WEEKDAY),
        ("営業時間（土曜）", ["Sa"]),
        ("営業時間（日祝）", ["Su"]),
    ):
        value = texts.get(label)
        if not value:
            continue
        value = value.strip()
        if value in ("休業", "定休"):
            oh.set_closed(days)
            continue

        # A few stores open later on Fridays: "6:30～21:00,金　6:30～22:00".
        if "金　" in value:
            base, _, friday = value.partition("金　")
            _add_hours(oh, days[:-1], base)
            _add_hours(oh, days[-1:], friday)
        else:
            _add_hours(oh, days, value)

    if not (oh_string := oh.as_opening_hours()):
        return None

    # 日祝 is the same hours as Sunday plus public holidays. OpeningHours has no
    # concept of PH, so append it to the Sunday group (same approach as sushiro_jp).
    groups = oh_string.split("; ")
    for index, group in enumerate(groups):
        day_part, _, hours = group.partition(" ")
        if "Su" in day_part:
            groups[index] = f"{day_part},PH {hours}"
            break
    return "; ".join(groups)


def _add_hours(oh: OpeningHours, days: list[str], value: str) -> None:
    # Ignore any trailing note: "（4月1日より…）" or "※一時閉店あり".
    value = re.split(r"[（※]", value, maxsplit=1)[0]
    # Normalise separators and whitespace: "6:20～10:00, 16:00-21:00", "6:50 ～22:00", "7:00~20:00".
    value = re.sub(r"[〜～~]", "-", value)
    value = re.sub(r"\s", "", value)
    for range_str in value.split(","):
        if m := re.fullmatch(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", range_str):
            open_time = _format_time(m.group(1))
            close_time = _format_time(m.group(2))
            oh.add_days_range(days, open_time, close_time, time_format="%H:%M")


def _format_time(time: str) -> str:
    hours, _, minutes = time.partition(":")
    return f"{int(hours):02d}:{minutes}"
