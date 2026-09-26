from typing import Any, AsyncIterator, Iterable
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import TextResponse
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class ElkjopNOSpider(CamoufoxSpider):
    name = "elkjop_no"
    item_attributes = {"name": "Elkjøp", "brand": "Elkjøp", "brand_wikidata": "Q1771628"}
    start_urls = ["https://www.elkjop.no/api/stores"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type != "document"
        and not request.url.startswith("https://www.elkjop.no/.well-known/vercel/security/"),
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            self.start_urls[0],
            meta={
                "dont_retry": True,
                "handle_httpstatus_list": [429],
                "camoufox_page_methods": [
                    # The Vercel security checkpoint answers the first request with an
                    # HTTP 429 challenge page, which reloads the real response once its
                    # proof-of-work solves.
                    PageMethod("wait_for_selector", "body > pre", timeout=90000),
                    PageMethod("evaluate", "() => JSON.parse(document.body.textContent)"),
                ],
            },
        )

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for store in response.meta["camoufox_page_methods"][1].result.get("data", {}).get("stores", []):
            item = DictParser.parse(store)

            item["branch"] = item.pop("name").removeprefix("Elkjøp ")

            if address := store.get("address"):
                item["housenumber"] = address.get("nr")
                if location := address.get("location"):
                    item["lat"] = location.get("lat")
                    item["lon"] = location.get("lng")

            if url := store.get("url"):
                item["website"] = urljoin("https://www.elkjop.no/", url)

            apply_category(Categories.SHOP_ELECTRONICS, item)

            yield item
