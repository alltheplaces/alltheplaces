from locations.storefinders.rio_seo import RioSeoSpider


class OldNavySpider(RioSeoSpider):
    name = "old_navy"
    item_attributes = {"brand": "Old Navy", "brand_wikidata": "Q2735242"}
    end_point = "https://oldnavy.gap.com/stores/maps"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
