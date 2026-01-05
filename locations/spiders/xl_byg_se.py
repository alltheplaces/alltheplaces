import json

import scrapy

from locations.dict_parser import DictParser


class XlBygSESpider(scrapy.Spider):
    name = "xl_byg_se"
    item_attributes = {"brand": "XL-Bygg", "brand_wikidata": "Q10720798"}
    start_urls = ["https://www.xlbygg.se/butiker/"]

    def parse(self, response, **kwargs):
        location_data = json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get())
        for store in location_data["props"]["pageProps"]["stores"]:
            store["street_address"] = store.pop("address")
            store.pop("region")
            item = DictParser.parse(store)
            item["website"] = response.urljoin(store.get("slug", ""))
            yield item
