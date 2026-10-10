from locations.categories import Categories, apply_category
from locations.storefinders.rio_seo import RioSeoSpider


class FannieMayUSSpider(RioSeoSpider):
    name = "fannie_may_us"
    item_attributes = {"brand": "Fannie May", "brand_wikidata": "Q5433964", "name": "Fannie May"}
    end_point = "https://maps.locations.fanniemay.com"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name", None)
        apply_category(Categories.SHOP_CHOCOLATE, feature)
        yield feature
