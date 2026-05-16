import json
from string import capwords

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class MatoppetSESpider(JSONBlobSpider):
    name = "matoppet_se"
    item_attributes = {
        "brand": "Matöppet",
        "brand_wikidata": "Q10578618",
    }
    start_urls = ["https://www.matoppet.se/butiker/"]

    def extract_json(self, response):
        return json.loads(response.css('script#locations[type="application/json"]::text').get())

    def pre_process_data(self, feature):
        feature["street_address"] = capwords(feature.pop("Street", "") or "")
        if city := feature.get("City"):
            feature["City"] = capwords(city)

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name", None)
        item["name"] = "Tempo"
        item["country"] = "SE"
        if store_link := location.get("StoreLinkString"):
            item["website"] = "https://www.matoppet.se" + store_link
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
