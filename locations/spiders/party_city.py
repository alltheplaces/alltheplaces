from locations.storefinders.rio_seo import RioSeoSpider


class PartyCitySpider(RioSeoSpider):
    name = "party_city"
    item_attributes = {"brand": "Party City", "brand_wikidata": "Q7140896"}
    end_point = "https://maps.partycity.com.qa.rioseo.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        if "genericImg" in feature["image"]:
            del feature["image"]
        yield feature
