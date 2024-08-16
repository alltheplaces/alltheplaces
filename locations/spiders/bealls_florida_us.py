from locations.storefinders.rio_seo import RioSeoSpider


class BeallsFloridaUSSpider(RioSeoSpider):
    name = "bealls_florida_us"
    item_attributes = {"brand": "Bealls", "brand_wikidata": "Q4876153"}
    end_point = "https://maps.stores.beallsflorida.com"

    def post_process_feature(self, feature, location):
        del feature["image"]
        yield feature
