import json
from string import capwords

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class HandlarnSeSpider(JSONBlobSpider):
    name = "handlarn_se"
    item_attributes = {
        "brand": "Handlar'n",
        "brand_wikidata": "Q10517161",
    }
    start_urls = ["https://www.handlarn.se/butiker-och-oppettider"]

    def extract_json(self, response):
        return json.loads(response.css('script#locations[type="application/json"]::text').get())

    def pre_process_data(self, feature):
        feature["street_address"] = capwords(feature.pop("Street", "") or "")
        if city := feature.get("City"):
            feature["City"] = capwords(city)

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name", None)
        item["name"] = "Handlar'n"
        item["country"] = "SE"
        if store_link := location.get("StoreLinkString"):
            item["website"] = "https://www.handlarn.se" + store_link
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
