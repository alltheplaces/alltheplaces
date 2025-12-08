from locations.storefinders.rio_seo import RioSeoSpider


class ApplebeesSpider(RioSeoSpider):
    name = "applebees"
    item_attributes = {"brand": "Applebee's Neighborhood Grill & Bar", "brand_wikidata": "Q621532"}
    end_point = "https://maps.restaurants.applebees.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        feature["website"] = feature["website"].replace(".com/", ".com/en-us/")
        feature["extras"]["website:menu"] = location["location_menu_link"]
        yield feature
