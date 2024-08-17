from locations.storefinders.rio_seo import RioSeoSpider


class EuropeanWaxCenterUSSpider(RioSeoSpider):
    name = "european_wax_center_us"
    item_attributes = {
        "brand_wikidata": "Q5413426",
        "brand": "European Wax Center",
    }
    domain = "locations.waxcenter.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
