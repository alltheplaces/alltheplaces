from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BlokkerNLSpider(Spider):
    name = "blokker_nl"
    item_attributes = {"brand": "Blokker", "brand_wikidata": "Q33903645"}
    start_urls = ["https://www.blokker.nl/nl/vind-een-winkel/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//*[@data-address]"):
            item = Feature()
            item["ref"] = location.xpath("./@data-id").get()
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-lng").get()
            item["branch"] = location.xpath("./@data-name").get("").strip().removeprefix("Blokker ")
            item["street_address"] = location.xpath("./@data-address").get()
            item["city"] = location.xpath("./@data-city").get()
            item["postcode"] = location.xpath("./@data-zip-code").get()
            item["website"] = response.urljoin(location.xpath("./@data-nav").get(""))
            apply_category(Categories.SHOP_HOUSEWARE, item)
            yield item
