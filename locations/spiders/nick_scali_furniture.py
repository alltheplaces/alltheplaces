import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class NickScaliFurnitureSpider(Spider):
    name = "nick_scali_furniture"
    item_attributes = {"brand": "Nick Scali", "brand_wikidata": "Q17053453"}
    allowed_domains = ["www.nickscali.com.au", "www.nickscali.co.nz"]
    start_urls = ["https://www.nickscali.com.au/showrooms", "https://www.nickscali.co.nz/showrooms"]

    def parse(self, response: TextResponse) -> Iterable[Feature | Request]:
        locations = json.loads(
            re.search(
                r"showrooms\":(\[.*\]),\"allShowroomPath",
                response.xpath('//*[contains(text(),"coordinate")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for store in locations:
            store.update(store.pop("fields"))
            store.update(store.pop("coordinate"))
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["name"] = self.item_attributes["brand"]
            item["website"] = response.urljoin(store.get("redirectUrl"))
            apply_category(Categories.SHOP_FURNITURE,item)
            yield item
