import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SteineckeDESpider(Spider):
    name = "steinecke_de"
    item_attributes = {"brand": "Steinecke", "brand_wikidata": "Q57516278"}
    start_urls = ["https://steinecke.de/baeckereien/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[contains(@class, "locations__grid-item")]'):
            item = Feature()
            item["branch"] = location.xpath("@data-name").get()
            item["ref"] = item["website"] = location.xpath('.//div[@class="locations__info__link"]/a/@href').get()
            item["lat"] = location.xpath("@data-lat").get()
            item["lon"] = location.xpath("@data-lng").get()
            item["street_address"] = location.xpath('.//div[@class="locations__info__address"]/text()').get()
            item["postcode"] = location.xpath("@data-postcode").get()
            item["city"] = location.xpath("@data-city").get()

            item["opening_hours"] = self.parse_opening_hours(json.loads(location.xpath("@data-opening-hours").get()))

            apply_category(Categories.SHOP_BAKERY, item)

            yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, hour_range in rules.items():
            if hour_range == "geschlossen":
                opening_hours.set_closed(day)
            elif hour_range:
                opening_hours.add_range(day, *hour_range.split("-"))
        return opening_hours
