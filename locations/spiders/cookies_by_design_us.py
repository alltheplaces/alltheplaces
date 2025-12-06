import json
from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class CookiesByDesignUSSpider(JSONBlobSpider):
    name = "cookies_by_design_us"
    item_attributes = {
        "brand": "Cookies by Design",
        "brand_wikidata": "Q5167112",
    }
    start_urls = [
        "https://sl.storeify.app/js/stores/cookiesbydesignprod.myshopify.com/storeifyapps-storelocator-geojson.js"
    ]

    def extract_json(self, response):
        return json.loads(response.text.removeprefix("eqfeed_callback(").removesuffix(")"))["features"]

    def pre_process_data(self, feature):
        feature.update(feature.pop("properties"))

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").split(" - ")[0]
        item["website"] = urljoin("https://www.cookiesbydesign.com", item["website"])

        oh = OpeningHours()
        oh.add_ranges_from_string(location["schedule_text"])
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_PASTRY, item)

        yield item
