from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class AvoskaRUSpider(JSONBlobSpider):
    name = "avoska_ru"
    item_attributes = {
        "brand": "Авоська",
        "extras": {
            "brand:en": "Avoska",
            "brand:ru": "Авоська",
        },
        # TODO: add wikidata
    }
    start_urls = ["https://www.avoska.ru/api/get_shops.php?map=1"]
    locations_key = "features"

    def post_process_item(self, item, response, location):
        # Coords are in the wrong order
        item["lat"] = location["geometry"]["coordinates"][0]
        item["lon"] = location["geometry"]["coordinates"][1]
        item["street_address"] = location["properties"]["hintContent"]
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
