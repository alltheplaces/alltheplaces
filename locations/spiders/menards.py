import json
from typing import AsyncIterator, Iterable

from scrapy.http import Request, TextResponse
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class MenardsSpider(JSONBlobSpider, CamoufoxSpider):
    name = "menards"
    item_attributes = {"brand": "Menards", "brand_wikidata": "Q1639897"}
    start_urls = ["https://www.menards.com/store-details/locator.html"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "script", "xhr", "fetch"],
        "CAMOUFOX_DEFAULT_NAVIGATION_TIMEOUT": 120000,
    }
    requires_proxy = True

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(
                url,
                meta={
                    "camoufox_page_methods": [
                        PageMethod("wait_for_selector", "meta#initialStores", state="attached", timeout=60000)
                    ],
                },
            )

    def extract_json(self, response: TextResponse) -> list[dict]:
        return json.loads(response.xpath("//@data-initial-stores").get())

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["number"]
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("street")
        item["website"] = f"https://www.menards.com/main/storeDetails.html?store={feature['number']}"
        apply_category(Categories.SHOP_DOITYOURSELF, item)

        yield item
