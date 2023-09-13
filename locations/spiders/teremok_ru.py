from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_RU, NAMED_DAY_RANGES_RU, OpeningHours


class TeremokRUSpider(scrapy.Spider):
    name = "teremok_ru"
    allowed_domains = ["teremok.ru"]
    item_attributes = {"brand": "Теремок", "brand_wikidata": "Q4455593"}
    start_urls = ["https://teremok.ru/"]

    def parse(self, response):
        city_selectors = response.xpath("//a[@class='b-geo__link b-link b-link--br-white b-link--thin js-city']")
        for city in city_selectors:
            city_id = city.xpath("@data-id").get()
            city_name = city.xpath("text()").get()
            yield JsonRequest(
                urljoin(self.start_urls[0], f"/api/place/list/?city_id={city_id}"),
                callback=self.parse_city,
                meta={"city_name": city_name},
            )

    def parse_city(self, response):
        city_name = response.meta["city_name"]
        for poi in response.json()["result"]["items"]:
            yield self.parse_poi(poi, city_name)

    def parse_poi(self, poi, city_name):
        item = DictParser.parse(poi)
        item["lat"], item["lon"] = poi.get("map", [None, None])
        item["city"] = city_name
        item["website"] = urljoin(self.start_urls[0], poi.get("url"))
        self.parse_hours(poi, item)
        return item

    def parse_hours(self, poi, item):
        if hours := poi.get("mode"):
            ranges = []
            for period in hours:
                days = period.get("days")
                time = period.get("time")
                ranges.append(f"{days}: {time}")
            try:
                oh = OpeningHours()
                oh.add_ranges_from_string("; ".join(ranges), DAYS_RU, NAMED_DAY_RANGES_RU)
                item["opening_hours"] = oh.as_opening_hours()
            except Exception:
                self.logger.warning(f"Parse hours failed: {hours}")
                self.crawler.stats.inc_value("atp/hours/failed")
