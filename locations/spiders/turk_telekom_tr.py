from typing import Any, AsyncIterator

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TurkTelekomTRSpider(scrapy.Spider):
    name = "turk_telekom_tr"
    item_attributes = {"brand": "Türk Telekom", "brand_wikidata": "Q263700"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        yield scrapy.http.JsonRequest(
            url="https://www.turktelekom.com.tr/_layouts/15/TTWebsite/Partners/Ajax.aspx/GetPartnersAll",
            data={"IsCorporate": "false"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in DictParser.get_nested_key(response.json(), "Data"):
            item = DictParser.parse(store)
            item["name"] = None
            item["phone"] = store["ContactTel"]
            item["lat"], item["lon"] = store["CoordinateX"], store["CoordinateY"]
            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            yield item
