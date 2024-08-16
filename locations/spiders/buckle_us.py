from locations.storefinders.rio_seo import RioSeoSpider


class BuckleUSSpider(RioSeoSpider):
    name = "buckle_us"
    item_attributes = {
        "brand_wikidata": "Q4983306",
        "brand": "Buckle",
    }
    end_point = "https://maps.local.buckle.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
