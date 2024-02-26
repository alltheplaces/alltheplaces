from urllib.parse import urljoin

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class ChetyreLapyRUSpider(scrapy.Spider):
    name = "chetyre_lapy_ru"
    allowed_domains = ["4lapy.ru"]
    start_urls = ["https://4lapy.ru/ajax/location/city/select/list/"]
    item_attributes = {"brand_wikidata": "Q62390783"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        html = response.json()["html"]
        selector = scrapy.Selector(text=html)
        city_codes = set(selector.xpath("//@data-code").getall())
        for code in city_codes:
            yield scrapy.Request(
                f"https://4lapy.ru/ajax/store/list/chooseCity/?code={code}",
                callback=self.parse_pois,
            )

    def parse_pois(self, response):
        for poi in response.json()["data"].get("items", []):
            if not poi["active"]:
                continue
            item = Feature()
            item["ref"] = poi["id"]
            item["addr_full"] = poi["addr"]
            item["phone"] = poi["phone"]
            item["lat"] = poi["gps_s"]
            item["lon"] = poi["gps_n"]
            item["image"] = urljoin("https://4lapy.ru/", poi["photo"])
            item["website"] = urljoin("https://4lapy.ru/shops/", item["ref"].lower())
            oh = OpeningHours()
            start, end = poi.get("schedule", "").replace(" ", "").split("-")
            oh.add_days_range(DAYS, start, end)
            item["opening_hours"] = oh.as_opening_hours()
            yield item
