from locations.storefinders.rio_seo import RioSeoSpider


class NinetynineCentsOnlyStoresUSSpider(RioSeoSpider):
    name = "99_cents_only_stores_us"
    item_attributes = {
        "brand_wikidata": "Q4646294",
        "brand": "99 Cents Only Stores",
    }
    end_point = "https://maps.locations.99only.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        del feature["image"]
        yield feature
