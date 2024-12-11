from typing import Iterable

from scrapy import Selector

from locations.categories import Categories
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class DuskNZSpider(AmastyStoreLocatorSpider):
    name = "dusk_nz"
    item_attributes = {"brand": "dusk", "brand_wikidata": "Q120669167", "extras": Categories.SHOP_HOUSEWARE.value}
    allowed_domains = ["www.duskcandles.co.nz"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["addr_full"] = clean_address(popup_html.xpath("//text()").getall())
        item["branch"] = item.pop("name")
        item["website"] = f'https://www.duskcandles.co.nz/store-locator/dusk-{item["branch"].lower()}/'
        yield item
