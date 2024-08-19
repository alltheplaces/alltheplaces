from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CooplandsGBSpider(WPStoreLocatorSpider):
    name = "cooplands_gb"
    item_attributes = {"brand": "Cooplands", "brand_wikidata": "Q5167971"}
    allowed_domains = ["cooplands-bakery.co.uk"]
    iseadgg_countries_list = ["GB"]
    search_radius = 50
    max_results = 50
    time_format = "%I:%M %p"

    # def parse_item(self, item, location):
    # item["addr_full"] = location["address"]
    # item.pop("street_address", None)
    # yield item
