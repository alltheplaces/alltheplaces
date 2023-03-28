from locations.storefinders.sweetiq import SweetIQSpider


class GolfTownCASpider(SweetIQSpider):
    name = "golf_town_ca"
    item_attributes = {"brand": "Golf Town", "brand_wikidata": "Q112966691"}
    start_urls = ["https://stores.golftown.com/"]

    def parse_item(self, item, location):
        item.pop("website")
        yield item
