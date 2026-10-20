from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BOT_USER_AGENT_SCRAPY


class GoldmarkAUSpider(JSONBlobSpider):
    name = "goldmark_au"
    item_attributes = {"brand": "Goldmark", "brand_wikidata": "Q17005474"}
    allowed_domains = ["www.goldmark.com.au"]
    start_urls = ["https://www.goldmark.com.au/stores/all-stores"]
    custom_settings = {"USER_AGENT": BOT_USER_AGENT_SCRAPY}

    def extract_json(self, response: Response) -> dict:
        stores_js = response.xpath('//script[contains(text(), "var go_stores = ")]/text()').get()
        locations = parse_js_object("{" + stores_js.split("{", 1)[1].split("};", 1)[0] + "}")
        return locations

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["storenumber"])
        item["branch"] = item.pop("name", None)
        item["opening_hours"] = OpeningHours()
        if item.get("website"):
            item["website"] = "https://{}/stores/".format(self.allowed_domains[0]) + item["website"]
        if feature.get("openhours"):
            hours_json = parse_js_object(feature["openhours"])
            hours_text = " ".join([f"{day_name}: {day_hours}" for day_name, day_hours in hours_json.items()])
            hours_text = hours_text.replace(" hours", "")
            item["opening_hours"].add_ranges_from_string(hours_text)
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
