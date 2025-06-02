from hashlib import sha1

from chompjs import parse_js_object

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class SupercorESSpider(JSONBlobSpider):
    name = "supercor_es"
    item_attributes = {"brand": "Supercor", "brand_wikidata": "Q6135841"}
    allowed_domains = ["www.supercor.es"]
    start_urls = ["https://www.supercor.es/tiendas/"]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def extract_json(self, response):
        js_blob = response.xpath('//script[contains(text(), "var tiendas = `")]/text()').get()
        js_blob = js_blob.split("var tiendas = `", 1)[1].split("`;", 1)[0]
        return parse_js_object(js_blob, unicode_escape=True)

    def post_process_item(self, item, response, location):
        # Ignore closed stores
        if location["abierto"] != "1":
            return

        # Coordinates are switched
        item["lat"] = location["coordenadax"]
        item["lon"] = location["coordenaday"]

        # Create a reference ID from the store address as this is the most
        # permanent identifier available to be used.
        item["ref"] = sha1(location["direccion"].encode("UTF-8")).hexdigest()
        item["postcode"] = location["cp"]

        if "Exprés" in item["name"].title():
            item["name"] = "Supercor Exprés"
        else:
            item["name"] = "Supercor"

        hours_text = " ".join(location["horario"]).replace(":|", ": ")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_ES)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
