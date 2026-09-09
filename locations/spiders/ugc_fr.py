import re
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class UgcFRSpider(Spider):
    name = "ugc_fr"
    item_attributes = {"brand": "UGC", "brand_wikidata": "Q1643241"}
    start_urls = ["https://www.ugc.fr/cinemasAjaxAction!getCinemasList.action"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for block in response.css("div.text-wrapper"):
            name = block.css(".block--title a::attr(title)").get()
            if not name:
                continue

            item = Feature()
            item["ref"] = block.css("a.add-to-fav::attr(data-fav-cinema-id)").get()
            item["name"] = name
            item["website"] = urljoin(response.url, block.css(".block--title a::attr(href)").get())

            address_lines = [line.strip() for line in block.css("p.address::text").getall() if line.strip()]
            if address_lines:
                item["street_address"] = address_lines[0]
                if len(address_lines) > 1:
                    if m := re.match(r"^(\d{5})\s+(.+)$", address_lines[-1]):
                        item["postcode"], item["city"] = m.groups()
                    else:
                        item["street_address"] = ", ".join(address_lines)
            item["country"] = "FR"

            apply_category(Categories.CINEMA, item)

            yield item
