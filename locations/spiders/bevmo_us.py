import json

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.camoufox_spider import CamoufoxSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class BevmoUSSpider(JSONBlobSpider, CamoufoxSpider):
    name = "bevmo_us"
    item_attributes = {"brand": "BevMo!", "brand_wikidata": "Q4899308"}
    start_urls = ["https://bevmo.com/pages/store-locator"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = "//a[@href='#MainContent']"
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def extract_json(self, response):
        script = response.xpath("//script[@defer='defer']/text()").get()
        if script is None:
            print(response.body)
        starter = "const locations = "
        begin = script.find(starter) + len(starter)
        end = script.find('";', begin + 1) + 1
        return json.loads(json.loads(script[begin:end]))

    def post_process_item(self, item, response, feature):
        item["street_address"] = feature["address_1"]
        item["ref"] = feature["bevmo_id"]
        item["branch"] = item.pop("name")

        fulfillment_modalities = feature["fulfillment_modalities"].split(",")
        apply_yes_no(Extras.TAKEAWAY, item, "pickup" in fulfillment_modalities)
        apply_yes_no(Extras.DELIVERY, item, "delivery" in fulfillment_modalities)

        oh = OpeningHours()
        for day in DAYS_FULL:
            hours = feature[f"hours_{day.lower()}"]
            oh.add_ranges_from_string(f"{day} {hours}")
        item["opening_hours"] = oh

        yield item
