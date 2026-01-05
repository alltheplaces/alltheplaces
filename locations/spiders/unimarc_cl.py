from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class UnimarcCLSpider(Spider):
    name = "unimarc_cl"
    item_attributes = {"brand": "Unimarc", "brand_wikidata": "Q6156244"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://cdn.contentful.com/spaces/un6yvtd6uq5z/environments/master/entries?content_type=sucursal&limit=1000",
            headers={"Authorization": "Bearer 1lMdSIz-dBxhYEwiRuKFXUl2AimjWZ04RDKeBx5mKq0"},
        )

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            store = location["fields"]
            store["street_address"] = store.pop("address")
            item = DictParser.parse(store)
            item["branch"] = store.get("storeName")
            item["city"] = store.get("comuna")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
