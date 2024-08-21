from locations.storefinders.rio_seo import RioSeoSpider


class SeesCandiesSpider(RioSeoSpider):
    name = "sees_candies"
    item_attributes = {"brand": "See's Candies", "brand_wikidata": "Q2103510"}
    end_point = "https://maps.sees.com"

    def post_process_feature(self, feature, location):
        if "Partner" in location["Location Type_CS"]:
            return

        feature["country"] = location["country_custom"]

        yield feature
