from scrapy import Selector

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class AussieDisposalsAUSpider(AmastyStoreLocatorSpider):
    name = "aussie_disposals_au"
    item_attributes = {"brand": "Aussie Disposals", "brand_wikidata": "Q117847729"}
    allowed_domains = ["www.aussiedisposals.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "AU"

    def parse_item(self, item, location, popup_html):
        item["street_address"] = item.pop("addr_full")
        item.pop("state")
        if location["state"] == "570":
            item["state"] = "NSW"
        elif location["state"] == "571":
            item["state"] = "VIC"
        elif location["state"] == "573":
            item["state"] = "SA"
        hours_string = " ".join(
            filter(None, Selector(text=location["description"]).xpath("//./span[@style]/text()").getall())
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
