from locations.storefinders.rio_seo_spider import RioSeoSpider


class SeesCandiesSpider(RioSeoSpider):
    name = "sees_candies"
    item_attributes = {"brand": "See's Candies", "brand_wikidata": "Q2103510"}
    allowed_domains = ["chocolateshops.sees.com"]
    start_urls = [
        "https://maps.sees.com/api/getAsyncLocations?template=domain&level=domain&search=66952&radius=10000&limit=3000"
    ]

    def post_process_feature(self, feature, location):
        feature["country"] = location["country_custom"]
        feature["extras"]["start_date"] = location["opening_date"]
        feature["located_in"] = location["location_shopping_center"]
