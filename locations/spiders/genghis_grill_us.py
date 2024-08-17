from locations.storefinders.rio_seo import RioSeoSpider


class GenghisGrillUSSpider(RioSeoSpider):
    name = "genghis_grill_us"
    item_attributes = {
        "brand_wikidata": "Q29470710",
        "brand": "Genghis Grill",
    }
    end_point = "https://maps.genghisgrill.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
