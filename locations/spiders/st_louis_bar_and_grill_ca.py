from locations.storefinders.sweetiq import SweetIQSpider


class StLouisBarAndGrillCASpider(SweetIQSpider):
    name = "st_louis_bar_and_grill_ca"
    item_attributes = {"brand": "St. Louis Bar & Grill", "brand_wikidata": "Q65567668"}
    start_urls = ["https://locations.stlouiswings.com/"]

    def parse_item(self, item, location):
        item.pop("email")
        item.pop("website")
        yield item
