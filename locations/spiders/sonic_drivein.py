from locations.storefinders.rio_seo import RioSeoSpider


class SonicDriveinSpider(RioSeoSpider):
    name = "sonic_drivein"
    item_attributes = {"brand": "Sonic Drive-In", "brand_wikidata": "Q7561808"}
    end_point = "https://maps.locations.sonicdrivein.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
