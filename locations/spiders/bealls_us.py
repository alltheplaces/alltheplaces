from locations.storefinders.rio_seo import RioSeoSpider


class BeallsUSSpider(RioSeoSpider):
    name = "bealls_us"
    item_attributes = {"brand": "Bealls", "brand_wikidata": "Q4876153"}
    end_point = "https://maps.stores.bealls.com"

    def post_process_feature(self, item, location):
        if item.get("image") and "_bealls_store_front.jpg" in item["image"]:
            # Generic brand image used instead of image of individual store.
            item.pop("image")
        yield item
