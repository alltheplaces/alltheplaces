from locations.storefinders.rio_seo import RioSeoSpider


class SpencersCAUSSpider(RioSeoSpider):
    name = "spencers_ca_us"
    item_attributes = {
        "brand_wikidata": "Q7576055",
        "brand": "Spencer Gifts",
    }
    end_point = "https://maps.spencersonline.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
