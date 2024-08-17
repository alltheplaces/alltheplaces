from locations.storefinders.rio_seo import RioSeoSpider


class AthletaSpider(RioSeoSpider):
    name = "athleta"
    item_attributes = {"brand": "Athleta", "brand_wikidata": "Q105722424"}
    end_point = "https://athleta.gap.com/stores/maps"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
