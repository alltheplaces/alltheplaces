from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.storefinders.amai_promap import AmaiPromapSpider


class KathmanduNZSpider(AmaiPromapSpider, PlaywrightSpider):
    name = "kathmandu_nz"
    item_attributes = {"brand": "Kathmandu", "brand_wikidata": "Q1736294"}
    start_urls = ["https://www.kathmandu.co.nz/pages/stores"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Kathmandu ")
        apply_category(Categories.SHOP_OUTDOOR, item)
        yield item
