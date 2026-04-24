from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LordOfTheFriesAUNZSpider(WPStoreLocatorSpider):
    name = "lord_of_the_fries_au_nz"
    item_attributes = {"brand": "Lord of the Fries", "brand_wikidata": "Q104088629"}
    allowed_domains = ["www.lordofthefries.com.au"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        sel = Selector(text=item.pop("name"))
        item["branch"] = sel.xpath("//a/text()").get()
        item["website"] = response.urljoin(sel.xpath("//a/@href").get())
        apply_category(Categories.FAST_FOOD, item)
        yield item
