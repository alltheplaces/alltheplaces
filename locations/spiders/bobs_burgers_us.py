import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BobsBurgersUSSpider(Spider):
    name = "bobs_burgers_us"
    item_attributes = {"name": "Bob's Burgers & Brew", "brand": "Bob's Burgers & Brew"}
    allowed_domains = ["www.bobsburgersandbrew.com"]
    start_urls = ["https://bobsburgersandbrew.com/bob-s-burgers-and-brew-locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for lat, lon, addr, ref in re.findall(
            r"lat: (-?\d+\.\d+),[\s\n]+?lng: (-?\d+\.\d+),[\s\n]+?zoom: 18,[\s\n]+?pinTitle: \"(.+?)\",[\s\n]+?pinLink: \".+?\",[\s\n]+?id: (\d+)",
            response.text,
        ):
            item = Feature(ref=ref, lat=lat, lon=lon, addr_full=addr)

            apply_category(Categories.RESTAURANT, item)

            yield item
