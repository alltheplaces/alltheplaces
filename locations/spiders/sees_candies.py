from locations.storefinders.rio_seo import RioSeoSpider


class SeesCandiesSpider(RioSeoSpider):
    name = "sees_candies"
    item_attributes = {"brand": "See's Candies", "brand_wikidata": "Q2103510"}
    allowed_domains = ["maps.sees.com"]
    start_urls = [
        "https://maps.sees.com/api/getAsyncLocations?template=search&level=search&search=Kansas%20City,%20KS,%20US&radius=100000&limit=100000"
    ]

    def post_process_feature(self, feature, location):
        if "Partner" in location["Location Type_CS"]:
            return

        feature["country"] = location["country_custom"]
        if location.get("opening_date"):
            feature["extras"]["start_date"] = location["opening_date"]
        feature["located_in"] = location["location_shopping_center"]

        yield feature
