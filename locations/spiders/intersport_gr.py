import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.linked_data_parser import LinkedDataParser


class IntersportGRSpider(scrapy.Spider):
    name = "intersport_gr"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://www.intersport.gr/el/etairia/katastimata/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[@data-control="box"]'):
            ld_item = json.loads(store.xpath('.//script[@type="application/ld+json"]/text()').get())
            item = LinkedDataParser.parse_ld(ld_item)
            item["lat"] = store.xpath(".//@data-latitude").get()
            item["lon"] = store.xpath(".//@data-longitude").get()
            item["ref"] = item["website"] = response.urljoin(
                store.xpath('.//a[contains(text(),"Περισσότερα")]/@href').get()
            )
            item["branch"] = store.xpath('.//li[@class="name"]/text()').get()
            item["name"] = None
            yield item
