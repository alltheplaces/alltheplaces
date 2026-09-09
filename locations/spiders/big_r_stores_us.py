import re

from chompjs import parse_js_object

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class BigRStoresUSSpider(JSONBlobSpider):
    """
    Big R Stores is a family-owned farm/ranch/home supply chain headquartered
    in Pueblo, CO, founded in 1962 in La Junta and Lamar, CO. It is unrelated
    to "Big R Farm and Home" (see big_r_farm_and_home_us.py), a much smaller,
    separately-owned chain based in Illinois that happens to share a similar
    name.

    Locations are sourced from a Google Maps Platform "Locator Plus" widget
    embedded on the site. The listing includes the company's Pueblo, CO home
    office, which is filtered out as it is not a retail store.
    """

    name = "big_r_stores_us"
    item_attributes = {"brand": "Big R Stores", "name": "Big R"}
    allowed_domains = ["storage.googleapis.com"]
    start_urls = ["https://storage.googleapis.com/maps-solutions-e51b6gp2we/locator-plus/gg37/locator-plus-config.js"]
    no_refs = True

    def extract_json(self, response):
        js_blob = "[" + response.text.split('"locations": [', 1)[1].split("],", 1)[0] + "]"
        return parse_js_object(js_blob)

    def post_process_item(self, item, response, location):
        if "Home Office" in location["title"]:
            # This is the corporate head office, not a retail store.
            return

        item.pop("name", None)
        item["branch"] = re.sub(r"^Big R\s*(?:Stores)?\s*-\s*", "", location["title"])
        item["addr_full"] = clean_address([location["address1"], location["address2"]])
        item["extras"]["ref:google:place_id"] = location.get("placeId")
        item["lat"] = location["coords"]["lat"]
        item["lon"] = location["coords"]["lng"]

        apply_category(Categories.SHOP_AGRARIAN, item)

        yield item
