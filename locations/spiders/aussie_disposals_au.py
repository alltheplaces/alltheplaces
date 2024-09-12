from typing import Iterable

from scrapy import Selector

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class AussieDisposalsAUSpider(AmastyStoreLocatorSpider):
    name = "aussie_disposals_au"
    item_attributes = {"brand": "Aussie Disposals", "brand_wikidata": "Q117847729"}
    allowed_domains = ["www.aussiedisposals.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "AU"

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item.pop("state")
        if feature["state"] == "570":
            item["state"] = "NSW"
        elif feature["state"] == "571":
            item["state"] = "VIC"
        elif feature["state"] == "573":
            item["state"] = "SA"
        hours_string = " ".join(
            filter(None, Selector(text=feature["description"]).xpath("//./span[@style]/text()").getall())
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
