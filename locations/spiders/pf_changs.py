from locations.storefinders.rio_seo import RioSeoSpider


class PfChangsSpider(RioSeoSpider):
    name = "pf_changs"
    item_attributes = {"brand": "P.F. Chang's", "brand_wikidata": "Q5360181"}
    end_point = "https://maps.locations.pfchangs.com"
    template = "search"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
