from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BreadtopAUSpider(WPStoreLocatorSpider):
    name = "breadtop_au"
    item_attributes = {"brand": "Breadtop", "brand_wikidata": "Q4959217"}
    allowed_domains = ["www.breadtop.com.au"]
    iseadgg_countries_list = ["AU"]
    search_radius = 200
    max_results = 50

    def parse_item(self, item, location):
        item["branch"] = item.pop("name", None)
        item["addr_full"] = item.pop("street_address", None)
        yield item
