from locations.storefinders.rio_seo import RioSeoSpider


class IhopSpider(RioSeoSpider):
    name = "ihop"
    item_attributes = {"brand": "IHOP", "brand_wikidata": "Q1185675"}
    end_point = "https://maps.restaurants.ihop.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
