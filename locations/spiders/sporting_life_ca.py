from locations.storefinders.sweetiq import SweetIQSpider


class SportingLifeCASpider(SweetIQSpider):
    name = "sporting_life_ca"
    item_attributes = {"brand": "Sporting Life", "brand_wikidata": "Q7579583"}
    start_urls = ["https://stores.sportinglife.ca/"]

    def parse_item(self, item, location):
        item.pop("email")
        item.pop("website")
        yield item
