from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider


class StrackAndVanTilUSSpider(StoreLocatorPlusSelfSpider):
    name = "strack_and_van_til_us"
    item_attributes = {
        "brand_wikidata": "Q17108969",
        "brand": "Strack & Van Til",
    }
    allowed_domains = ["strackandvantil.com"]
    iseadgg_countries_list = ["US"]
    search_radius = 500
    max_results = 100

    def parse_item(self, item, location):
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name
        yield item
