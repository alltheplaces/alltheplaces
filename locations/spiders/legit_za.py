from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.storefinders.amai_promap import AmaiPromapSpider


class LegitZASpider(AmaiPromapSpider, PlaywrightSpider):
    name = "legit_za"
    start_urls = ["https://www.legit.co.za/pages/store-locator"]
    item_attributes = {"brand": "LEGiT", "brand_wikidata": "Q122959274"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
