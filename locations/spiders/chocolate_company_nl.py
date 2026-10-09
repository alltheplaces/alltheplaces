from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ChocolateCompanyNLSpider(WPStoreLocatorSpider):
    name = "chocolate_company_nl"
    item_attributes = {"brand": "Chocolate Company", "brand_wikidata": "Q108926938"}
    allowed_domains = ["choco.piranha-dev.online"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.CAFE, item)
        yield item
