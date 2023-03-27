from locations.storefinders.sweetiq import SweetIQSpider


class ThePaperStoreUSSpider(SweetIQSpider):
    name = "the_paper_store_us"
    item_attributes = {"brand": "The Paper Store", "brand_wikidata": "Q65068381"}
    start_urls = ["https://locations.thepaperstore.com/"]

    def parse_item(self, item, location):
        item.pop("name")
        item.pop("email")
        if item["website"] == "https://www.thepaperstore.com":
            item.pop("website")
        yield item
