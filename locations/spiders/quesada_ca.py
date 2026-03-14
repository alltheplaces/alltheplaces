from locations.storefinders.sweetiq import SweetIQSpider


class QuesadaCASpider(SweetIQSpider):
    name = "quesada_ca"
    item_attributes = {"brand": "Quesada", "brand_wikidata": "Q66070360"}
    start_urls = ["https://locations.quesada.ca/"]
    custom_settings = {"DOWNLOAD_DELAY": 2}

    def parse_item(self, item, location, **kwargs):
        item.pop("email")
        item.pop("website")
        yield item
