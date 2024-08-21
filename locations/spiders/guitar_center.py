from locations.storefinders.rio_seo import RioSeoSpider


class GuitarCenterSpider(RioSeoSpider):
    name = "guitar_center"
    item_attributes = {"brand": "Guitar Center", "brand_wikidata": "Q3622794"}
    end_point = "https://maps.stores.guitarcenter.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
