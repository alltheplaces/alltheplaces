import json
import re

from scrapy.http import TextResponse
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class FootasylumGBSpider(Spider):
    name = "footasylum_gb"
    item_attributes = {"brand": "Footasylum", "brand_wikidata": "Q126913565"}
    start_urls = ["https://www.footasylum.com/store-locator/"]

    def parse(self, response: TextResponse):
        json_data = json.loads(
            re.search(
                r"stores\":(\[.*\]),\"global\"",
                response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for store in json_data:
            item = DictParser.parse(store)
            item["street_address"] = store.get("location").get("address")[0]
            item["addr_full"] = merge_address_lines(store.get("location").get("address"))
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(item.get("website"))
            yield item
