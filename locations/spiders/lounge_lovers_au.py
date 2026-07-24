from typing import Iterable

from scrapy import Selector
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class LoungeLoversAUSpider(AmastyStoreLocatorSpider):
    name = "lounge_lovers_au"
    item_attributes = {"brand": "Lounge Lovers", "brand_wikidata": "Q140684820"}
    allowed_domains = ["www.loungelovers.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Request]:
        yield Request(url=item["website"].removesuffix("/"), callback=self.parse_store_page)

    def parse_store_page(self, response: Response) -> Iterable[Feature]:
        item = LinkedDataParser.parse(response, "Store")
        item["ref"] = response.url
        item["branch"] = item.pop("name", None)
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
