import re
from typing import Any, Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BOT_USER_AGENT_SCRAPY


class AngusAndCooteAUSpider(JSONBlobSpider):
    name = "angus_and_coote_au"
    item_attributes = {"brand": "Angus and Coote", "brand_wikidata": "Q18162112"}
    allowed_domains = ["www.anguscoote.com.au"]
    start_urls = ["https://www.anguscoote.com.au/stores/all-stores"]
    custom_settings = {"USER_AGENT": BOT_USER_AGENT_SCRAPY}

    def extract_json(self, response):
        stores_js = response.xpath('//script[contains(text(), "var go_stores = ")]/text()').get()
        locations = parse_js_object("{" + stores_js.split("{", 1)[1].split("};", 1)[0] + "}")
        for location_id, location in locations.items():
            if location.get("rawdata"):
                raw_data = parse_js_object(location.get("rawdata"))
                location["street_address"] = re.sub(
                    r"\s+",
                    " ",
                    ", ".join(
                        filter(
                            None,
                            [
                                raw_data.get("Address line 1"),
                                raw_data.get("Address line 2"),
                                raw_data.get("Address line 3"),
                                raw_data.get("Address line 4"),
                                raw_data.get("Address line 5"),
                            ],
                        )
                    ).strip(),
                )
                location["city"] = raw_data.get("Locality")
                location["postcode"] = raw_data.get("Postcode")
        return locations.values()

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item["state"] = location.get("regioncode")
        item["addr_full"] = re.sub(r"\s+", " ", item.get("addr_full", ""))
        item["website"] = "https://www.anguscoote.com.au/stores/" + location.get("url")
        if location.get("openhours"):
            hours_json = parse_js_object(location["openhours"])

            item["opening_hours"] = OpeningHours()
            hours_text = ""
            for day_name in DAYS_FULL:
                if hours_range := hours_json.get("{} hours".format(day_name.title())):
                    hours_text = f"{hours_text} {day_name}: {hours_range}"
            item["opening_hours"].add_ranges_from_string(hours_text)

        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
