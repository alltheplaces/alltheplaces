from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

SLOVENSKA_POSTA = {"operator": "Slovenská pošta", "operator_wikidata": "Q1191849"}
BALIKOBOX = {"brand": "BalíkoBOX", "brand_wikidata": "Q131136953", **SLOVENSKA_POSTA}


class SlovenskaPostaSKSpider(Spider):
    name = "slovenska_posta_sk"
    start_urls = ["https://www.posta.sk/pobocky-a-balikoboxy"]
    api_url = "https://api.posta.sk/private/web/branches"
    page_size = 100

    async def start(self) -> AsyncIterator[Request]:
        yield self.request_page(0)

    def request_page(self, offset: int) -> Request:
        return Request(
            url="{}?{}".format(
                self.api_url, urlencode({"include": "detail", "limit": self.page_size, "offset": offset})
            ),
            cb_kwargs={"offset": offset},
        )

    def parse(self, response: Response, offset: int, **kwargs: Any) -> Any:
        locations = response.json().get("branches", [])
        for location in locations:
            item = self.parse_location(location)

            if location.get("kind") == "office":
                item.update(SLOVENSKA_POSTA)
                apply_yes_no(Extras.ATM, item, "atm" in location.get("services", []))
                apply_category(Categories.POST_OFFICE, item)
            elif location.get("kind") == "bbox" and location.get("name", "").startswith("BalíkoBOX"):
                item.update(BALIKOBOX)
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                continue

            yield item

        if len(locations) == self.page_size:
            yield self.request_page(offset + self.page_size)

    def parse_location(self, location: dict[str, Any]) -> Feature:
        item = DictParser.parse(location)

        item["ref"] = location["id"]
        item["lat"], item["lon"] = location["gps"]
        item["name"] = location.get("dname") or location.get("name")
        item["street_address"] = item.pop("street", None)
        item["city"] = location.get("city")
        item["postcode"] = location.get("zip")
        item["website"] = "https://www.posta.sk/pobocky-a-balikoboxy#{}".format(urlencode({"n": location["nsk"]}))

        if phones := location.get("phones"):
            item["phone"] = "; ".join(phones)

        item["opening_hours"] = self.parse_opening_hours(location.get("oh", []))

        return item

    def parse_opening_hours(self, days: list[dict[str, Any]]) -> OpeningHours | None:
        try:
            day_hours = {}
            for day in days:
                if not day.get("std"):
                    continue
                # The API repeats today's row before the standard week; keep the later weekly row.
                day_hours[DAYS_EN[day["day"].title()]] = day["std"]

            opening_hours = OpeningHours()
            for day, hours in day_hours.items():
                for open_seconds, close_seconds in hours:
                    opening_hours.add_range(day, self.format_seconds(open_seconds), self.format_seconds(close_seconds))
            return opening_hours
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def format_seconds(seconds: int) -> str:
        hours, remainder = divmod(seconds, 3600)
        return f"{hours:02}:{remainder // 60:02}"
