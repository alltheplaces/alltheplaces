from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class BancaSellaITSpider(JSONBlobSpider):
    name = "banca_sella_it"
    item_attributes = {"brand": "Banca Sella", "brand_wikidata": "Q3633749"}
    start_urls = ["https://www.sella.it/banca-online/store-locator/store-list.jsp"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = "stores"
    no_refs = True

    def post_process_item(self, item, response, location):
        item["city"] = location.get("citta")
        item["postcode"] = location.get("cap")
        apply_category(Categories.BANK, item)
        yield item
