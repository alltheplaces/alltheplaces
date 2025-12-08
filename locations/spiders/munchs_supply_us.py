import re
from typing import Iterable

from scrapy import Selector

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class MunchsSupplyUSSpider(AmastyStoreLocatorSpider):
    name = "munchs_supply_us"
    item_attributes = {"brand": "Munch's Supply", "brand_wikidata": "Q117021522"}
    allowed_domains = ["www.munchsupply.com"]

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        contact_raw_parts = popup_html.xpath(
            '//div[contains(@class, "amlocator-title")]/following-sibling::text()'
        ).getall()
        address_parts = []
        for contact_raw_part in contact_raw_parts:
            if m := re.match(r"^\s*ph:\s*([+\d\- ()]+)\s*$", contact_raw_part):
                item["phone"] = m.group(1)
            else:
                address_parts.append(contact_raw_part)
        item["addr_full"] = clean_address(address_parts)
        yield item
