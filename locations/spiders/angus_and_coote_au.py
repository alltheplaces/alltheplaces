import re

from chompjs import parse_js_object

from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class AngusAndCooteAUSpider(JSONBlobSpider):
    name = "angus_and_coote_au"
    item_attributes = {"brand": "Angus & Coote", "brand_wikidata": "Q18162112"}
    allowed_domains = ["www.anguscoote.com.au"]
    start_urls = ["https://www.anguscoote.com.au/stores/all-stores"]

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

    def post_process_item(self, item, response, location):
        item["addr_full"] = re.sub(r"\s+", " ", item.get("addr_full", ""))
        item["website"] = "https://www.anguscoote.com.au/stores/" + location.get("url")
        if location.get("rawdata"):
            raw_data = parse_js_object(location.get("rawdata"))

            item["opening_hours"] = OpeningHours()
            hours_text = ""
            for day_name in DAYS_FULL:
                if raw_data.get("{} hours".format(day_name.title())):
                    hours_range = raw_data.get("{} hours".format(day_name.title()))
                    hours_text = f"{hours_text} {day_name}: {hours_range}"
            item["opening_hours"].add_ranges_from_string(hours_text)

        yield item
