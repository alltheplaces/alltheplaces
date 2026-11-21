from typing import Iterable

from scrapy import Request, Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class Studio88Spider(AmastyStoreLocatorSpider):
    name = "studio_88"
    item_attributes = {"brand": "Studio 88", "brand_wikidata": "Q116498145"}
    allowed_domains = ["www.studio-88.co.za"]
    pagination_mode = True
    requires_proxy = "ZA"
    skip_auto_cc_domain = True

    def post_process_item(
        self, item: Feature, feature: dict, popup_html: Selector | None = None
    ) -> Iterable[Feature | Request]:
        name = item.pop("name", "")
        if name:
            item["branch"] = name.removeprefix("Studio 88 ")
        if popup_html is not None:
            address = clean_address(
                popup_html.xpath(
                    '//div[contains(@class, "s2")]//div[contains(@class, "amlocator-today")]/text()'
                ).getall()
            )
            if address:
                item["addr_full"] = address
            if phone := popup_html.xpath('//a[@class="phones"]/@href').get():
                item["phone"] = phone
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
