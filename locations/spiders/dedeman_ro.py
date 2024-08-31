from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class DedemanROSpider(Spider):
    name = "dedeman_ro"
    item_attributes = {"brand": "Dedeman", "brand_wikidata": "Q5249762"}
    start_urls = ["https://www.dedeman.ro/ro/suport-clienti/magazine-dedeman"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//div[@data-source-code]"):
            item = Feature()
            item["ref"] = location.xpath("@data-source-code").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["branch"] = location.xpath('.//p[@class="dedeman-network-store-list-item-name"]/text()').get()
            item["addr_full"] = location.xpath(
                './/div[@class="dedeman-network-store-list-item-address"]/span/text()'
            ).get()

            yield item
