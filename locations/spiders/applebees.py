from locations.storefinders.rio_seo import RioSeoSpider


class ApplebeesSpider(RioSeoSpider):
    name = "applebees"
    item_attributes = {
        "brand_wikidata": "Q621532",
        "brand": "Applebee's Neighborhood Grill & Bar",
    }
    end_point = "https://maps.restaurants.applebees.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
