import html

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours


class LewiatanPLSpider(Spider):
    name = "lewiatan_pl"
    item_attributes = {"brand": "Lewiatan", "brand_wikidata": "Q11755396"}
    start_urls = ["https://www.lewiatan.pl/api/stores"]

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["operator"] = html.unescape(item.pop("name"))
            item["street_address"] = item.pop("addr_full")
            item["website"] = response.urljoin(location["url"])
            if " (" in item["city"]:
                item["city"] = item["city"].split(" (")[0]
            apply_category(Categories.SHOP_SUPERMARKET, item)

            oh = self.parse_hours(location)
            if oh.day_hours:
                item["opening_hours"] = oh

            if item.get("phone") == "BRAK":  # 300 x "missing"
                item["phone"] = None

            yield item

    @staticmethod
    def parse_hours(location: dict) -> OpeningHours:
        # Sunday fields (3, 4) are for trading / non-trading Sundays only, so are not regular weekly hours
        oh = OpeningHours()
        for key, days in (
            ("field_open_hours_1_value", DAYS_WEEKDAY),
            ("field_open_hours_2_value", ["Sa"]),
        ):
            if hours := location.get(key):
                oh.add_days_range(days, *hours.split())
        return oh
