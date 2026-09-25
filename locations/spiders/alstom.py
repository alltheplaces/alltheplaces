from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class AlstomSpider(scrapy.Spider):
    name = "alstom"
    item_attributes = {"brand": "Alstom", "brand_wikidata": "Q309084"}
    allowed_domains = ["alstom.com"]
    start_urls = ("https://www.alstom.com/alstom-page/maps/json/1826",)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country in response.json():
            for location in country["locations"].values():
                item = Feature(
                    ref=location["id"],
                    branch=location["title"],
                    addr_full=location["address"],
                    country=country["name"],
                    phone=(location["phone"] or "").removeprefix("Phone: ") or None,
                    lat=location["lat"],
                    lon=location["long"],
                )
                apply_category(Categories.OFFICE_ENGINEER, item)
                yield item
