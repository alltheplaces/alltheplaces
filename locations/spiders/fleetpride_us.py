from locations.categories import Categories, apply_category
from locations.storefinders.rio_seo import RioSeoSpider


class FleetprideUSSpider(RioSeoSpider):
    name = "fleetpride_us"
    end_point = "https://maps.branches.fleetpride.com"

    def post_process_feature(self, feature, location):
        if "Service" in location["Store Type_CS"]:
            apply_category(Categories.SHOP_CAR_REPAIR, feature)
        elif "Parts" in location["Store Type_CS"]:
            apply_category(Categories.SHOP_CAR_PARTS, feature)
        if "Affiliates" not in location["Store Type_CS"]:
            feature["brand"] = "FleetPride"
            feature["brand_wikidata"] = "Q121436710"
        yield feature
