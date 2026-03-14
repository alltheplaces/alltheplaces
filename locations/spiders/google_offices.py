from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class GoogleOfficesSpider(Spider):
    name = "google_offices"
    allowed_domains = ["about.google"]
    item_attributes = {
        "brand": "Google",
        "brand_wikidata": "Q95",
    }
    start_urls = ["https://about.google/company-info/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//*[@data-city-name]"):
            item = Feature()
            item["city"] = location.xpath("./@data-city-name").get()
            item["ref"] = item["branch"] = (
                location.xpath(".//@data-building-name").get("").strip().removeprefix("Google ")
            )
            item["addr_full"] = location.xpath('.//*[contains(@class, "location-address")]/text()').get()
            item["lat"], item["lon"] = location.xpath(".//@data-coords").get("").split(",")
            item["image"] = location.xpath('.//img[@class="image"]/@src').get("").split("=")[0]
            apply_category(Categories.OFFICE_COMPANY, item)
            yield item
