from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LewisStoresSpider(JSONBlobSpider):
    name = "lewis_stores"
    item_attributes = {"brand": "Lewis Stores", "brand_wikidata": "Q115117217"}
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Referer": "https://www.lewisstores.co.za/"}}
    country_codes = ["za", "bw", "na", "sz", "ls"]

    async def start(self) -> AsyncIterator[Request]:
        for country_code in self.country_codes:
            yield Request(url=f"https://www.lewisstores.co.{country_code}/rest/V1/user-journey/store-location/get-all/")

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["email"] = None
        item["branch"] = item.pop("name").removeprefix("Lewis ")
        apply_category(Categories.SHOP_FURNITURE, item)

        yield item
