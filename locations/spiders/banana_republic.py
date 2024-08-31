from locations.storefinders.rio_seo import RioSeoSpider


class BananaRepublicSpider(RioSeoSpider):
    name = "banana_republic"
    item_attributes = {"brand": "Banana Republic", "brand_wikidata": "Q806085"}
    end_point = "https://bananarepublic.gap.com/stores/maps"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name")
        yield feature
