import scrapy
from scrapy.http import JsonRequest

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class BurgerKingRUSpider(scrapy.Spider):
    name = "burger_king_ru"
    item_attributes = {"brand": "Бургер Кинг", "brand_wikidata": "Q177054"}
    allowed_domains = ["burgerkingrus.ru"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        yield JsonRequest(
            "https://orderapp.burgerkingrus.ru/api/v1/restaurants/search",
            headers={"Origin": "https://burgerkingrus.ru", "Referer": "https://burgerkingrus.ru/"},
        )

    def parse(self, response):
        for poi in response.json().get("response"):
            item = DictParser.parse(poi)
            item["phone"] = poi.get("phone", "").replace(":", "")
            self.parse_hours(item, poi)
            apply_yes_no("internet_access=wlan", item, poi.get("wifi") == "1")
            apply_yes_no("drive_through", item, poi.get("king_drive") == "1")
            yield item

    def parse_hours(self, item, poi):
        oh = OpeningHours()
        open, close = poi.get("open_time"), poi.get("close_time")
        if open and close:
            oh.add_days_range(DAYS, open, close)
            item["opening_hours"] = oh.as_opening_hours()
