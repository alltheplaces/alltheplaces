import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.linked_data_parser import LinkedDataParser


class IntersportGRSpider(Spider):
    name = "intersport_gr"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://www.intersport.gr/el/etairia/katastimata/"]
    requires_proxy = True  # Akamai Bot Protection

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[@data-control="box"]'):
            item = LinkedDataParser.parse_ld(
                json.loads(store.xpath('.//script[@type="application/ld+json"]/text()').get())
            )
            item["name"] = item["email"] = item["phone"] = None
            item["lat"] = store.xpath(".//@data-latitude").get()
            item["lon"] = store.xpath(".//@data-longitude").get()
            item["ref"] = item["website"] = response.urljoin(
                store.xpath('.//a[contains(text(), "Περισσότερα")]/@href').get()
            )
            item["branch"] = store.xpath('.//li[@class="name"]/text()').get()
            yield item
