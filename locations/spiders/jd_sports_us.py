from locations.storefinders.rio_seo import RioSeoSpider


class JdSportsUSSpider(RioSeoSpider):
    name = "jd_sports_us"
    item_attributes = {
        "brand_wikidata": "Q6108019",
        "brand": "JD Sports",
    }
    end_point = "https://maps.stores.jdsports.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = location["location_display_name"]
        yield feature
