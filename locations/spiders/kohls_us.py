from locations.storefinders.rio_seo import RioSeoSpider


class KohlsUSSpider(RioSeoSpider):
    name = "kohls_us"
    item_attributes = {"brand": "Kohl's", "brand_wikidata": "Q967265"}
    end_point = "https://maps.kohlslocal.com"
    template = "search"

    def post_process_feature(self, feature, location):
        feature["branch"] = feature.pop("name").removeprefix("Kohl's ")
        feature["website"] = f"https://www.kohls.com{feature['website']}"
        yield feature
