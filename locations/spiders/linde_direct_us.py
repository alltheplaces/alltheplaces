from locations.storefinders.rio_seo import RioSeoSpider


class LindeDirectUSSpider(RioSeoSpider):
    name = "linde_direct_us"
    item_attributes = {"brand": "Linde", "brand_wikidata": "Q902780"}
    end_point = "https://maps.stores.lindedirect.com"

    def post_process_feature(self, feature, location):
        feature["extras"]["ref:google"] = location.get("google_place_id")
        yield feature
