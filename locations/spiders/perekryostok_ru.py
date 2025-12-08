import json
from urllib.parse import unquote

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class PerekryostokRUSpider(scrapy.Spider):
    name = "perekryostok_ru"
    item_attributes = {"brand": "Перекрёсток", "brand_wikidata": "Q1684639"}
    start_urls = ["https://www.perekrestok.ru/shops"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "RU"
    api_token = ""

    def parse(self, response):
        if not self.api_token:
            cookie = response.headers.to_unicode_dict().get("Set-Cookie")
            session = json.loads(unquote(cookie.split(";")[0]).replace("session=", ""))
            self.api_token = session["accessToken"]
        yield from self.fetch_pois_for_page()

    def fetch_pois_for_page(self, page=1):
        yield JsonRequest(
            url=f"https://www.perekrestok.ru/api/customer/1.4.1.0/shop?orderBy=id&orderDirection=asc&page={page}&perPage=100",
            headers={"Authorization": f"Bearer {self.api_token}"},
            callback=self.parse_pois,
        )

    def parse_pois(self, response):
        for poi in response.json()["content"]["items"]:
            item = DictParser.parse(poi)
            item["geometry"] = poi.get("location")
            item["city"] = poi.get("city").get("name")
            item["website"] = f'https://www.perekrestok.ru/shops/shop/{item["ref"]}'
            self.parse_hours(item, poi)
            apply_yes_no(Extras.DELIVERY, item, poi.get("isDeliveryAvailable"))
            apply_yes_no(Extras.TAKEAWAY, item, poi.get("isPickupAvailable"))
            yield item

        paginator = response.json()["content"]["paginator"]
        if paginator.get("nextPageExists"):
            yield from self.fetch_pois_for_page(paginator.get("current") + 1)

    def parse_hours(self, item, poi):
        def sanitize_time(s: str):
            return s.replace(" ", "").replace(".", ":").strip()

        if schedule := poi.get("schedule", ""):
            oh = OpeningHours()
            if schedule.lower().strip() in ["круглосуточно", "круглосуточный"]:
                item["opening_hours"] = "24/7"
                return
            try:
                open, close = sanitize_time(schedule).split("-")
                oh.add_days_range(DAYS, open, close)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {schedule}, {e}")
