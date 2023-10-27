from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CareOneUSSpider(WPStoreLocatorSpider):
    name = "careone_us"
    item_attributes = {"brand": "CareOne", "brand_wikidata": "Q25108589"}
    allowed_domains = ["www.care-one.com"]
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        item.pop("addr_full", None)
        yield item
