from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature

BRANDS = {
    "CocciMarket": {"brand": "CocciMarket", "brand_wikidata": "Q90020480"},
    "CocciMarket City - Easy": {"brand": "CocciMarket City", "brand_wikidata": "Q90020481"},
    "Coccinelle Express": {"brand": "Coccinelle Express", "brand_wikidata": "Q90020479"},
    "Coccinelle Supermarché": {"brand": "Coccinelle Supermarché", "brand_wikidata": "Q90020459"},
}


class CoccinelleFRSpider(Spider):
    name = "coccinelle_fr"
    start_urls = ["https://www.coccinelle.fr/data/locations.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("/markers/marker"):
            item = Feature()
            item["lat"] = location.xpath("@lat").get()
            item["lon"] = location.xpath("@lng").get()
            item["street_address"] = location.xpath("@address").get()
            item["city"] = location.xpath("@city").get()
            item["postcode"] = location.xpath("@postal").get()
            item["country"] = location.xpath("@country").get()
            item["phone"] = location.xpath("@phone").get()
            item["email"] = location.xpath("@email").get()
            item["ref"] = item["website"] = response.urljoin(location.xpath("@web").get())

            if b := BRANDS.get(location.xpath("@category").get()):
                item.update(b)
            else:
                self.logger.error("Unexpected type: {}".format(location.xpath("@category").get()))

            yield item
