from typing import Iterable, Any

from scrapy import Request
from scrapy.http import TextResponse, Response

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.spiders.shell import ShellSpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

DUCK_THRU = {"brand": "Duck Thru", "brand_wikidata": "Q139631383"}


class DuckThruUSSpider(WPStoreLocatorSpider):
    name = "duck_thru_us"
    allowed_domains = ["duckthru.com"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        yield Request(item["website"], callback=self.parse_page, cb_kwargs={"shop": item.deepcopy()})

        item["ref"] = item.pop("name").removeprefix("Duck Thru #")
        item.update(DUCK_THRU)
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item

    def parse_page(self, response: Response, shop: Feature, **kwargs: Any) -> Any:
        item = Feature(
            lat=shop["lat"],
            lon=shop["lon"],
            country=shop["country"],
            postcode=shop["postcode"],
            state=shop["state"],
            street_address=shop["street_address"],
            ref=response.url
        )

        if (
            brand := response.xpath('//p[contains(text(), "Brand:")]/text()')
            .get(default="")
            .removeprefix("Brand:")
            .strip()
        ):
            if brand == "Duck Thru":
                item.update(DUCK_THRU)
                item["website"] = response.url
            elif brand == "Shell":
                item.update(ShellSpider.item_attributes)
            else:
                item["brand"] = brand

        apply_category(Categories.FUEL_STATION, item)
        yield item
