from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class IsolaTesoriITSpider(JSONBlobSpider):
    name = "isola_tesori_it"
    item_attributes = {
        "brand": "L'Isola dei Tesori",
        "brand_wikidata": "Q108578003",
        "extras": Categories.SHOP_PET.value
    }
    start_urls = ["https://www.isoladeitesori.it/on/demandware.store/Sites-idt-it-Site/it_IT/Stores-FindStores"]
    locations_key = "stores"

    def post_process_item(self, item, response, location):
        item["extras"]["addr:province"] = item.pop("state")
        item["branch"] = item["name"]
        item["name"] = self.item_attributes["brand"]
        item["website"] = f"https://www.isoladeitesori.it/store/{item['website']}.html"
        yield item
