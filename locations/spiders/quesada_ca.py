from locations.storefinders.sweetiq import SweetIQSpider


class QuesadaCASpider(SweetIQSpider):
    name = "quesada_ca"
    item_attributes = {"brand": "Quesada", "brand_wikidata": "Q66070360"}
    start_urls = ["https://locations.quesada.ca/"]
    download_delay = 2.0

    def parse_item(self, item, location):
        item.pop("email")
        item.pop("website")
        yield item
