import re
from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class UltaBeautyUSSpider(UberallSpider):
    name = "ulta_beauty_us"
    item_attributes = {"brand": "Ulta Beauty", "brand_wikidata": "Q7880076"}
    key = "oSecJC6yCWx2PYWYQ6tVwe54NyHGPh"
    store_pages: dict[str, str] = {}

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.ulta.com/stores/sitemap.xml", callback=self.parse_sitemap)

    def parse_sitemap(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath("//*[local-name()='loc']/text()").getall():
            if m := re.search(r"/stores/(?!l/)[a-z0-9-]+-(\d+)$", url):
                self.store_pages[m.group(1)] = url
        yield JsonRequest(f"https://uberall.com/api/storefinders/{self.key}/locations/all")

    def pre_process_data(self, location: dict, **kwargs: Any) -> None:
        if location["phone"] and location["phone"].endswith("888-888-8888"):
            location["phone"] = None

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        if location["openingHoursNotes"] == "Coming Soon":
            return
        item["website"] = self.store_pages.get(item["ref"])
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
