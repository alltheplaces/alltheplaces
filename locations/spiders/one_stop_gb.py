from chompjs import chompjs
from scrapy import FormRequest, Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class OneStopGBSpider(Spider):
    name = "one_stop_gb"
    item_attributes = {"brand": "One Stop", "brand_wikidata": "Q65954217"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        # 100000 431
        # 50000  698
        # 10000  957
        for city in city_locations("GB", 10000):
            yield FormRequest(
                url="https://www.onestop.co.uk/wp-admin/admin-ajax.php",
                formdata={"action": "storefinder_ajax", "search": city["name"], "security": "f4350888a1"},
            )

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(response.text)
        if not data:
            return
        for location in data["message"]["locations"]:
            if location.get("location").get("address").get("details"):
                location["location"]["address"] = location.get("location").get("address").pop("details")
                location["location"]["address"]["street_address"] = merge_address_lines(
                    location["location"]["address"]["lines"]
                )
            location["location"]["contact"]["phone"] = location["location"]["contact"]["phoneNumbers"]["main"]
            item = DictParser.parse(location["location"])
            item["website"] = f'https://www.onestop.co.uk/store/?store={item["ref"]}'
            if isinstance(location["location"]["openingHours"], dict):
                item["opening_hours"] = OpeningHours()
                for day, intervals in location["location"]["openingHours"]["standard"].items():
                    for interval in intervals["intervals"]:
                        item["opening_hours"].add_range(day, interval["start"], interval["end"].strip("+"))

            facilities = [f["type"] for f in location["location"]["facilities"]]
            apply_yes_no(Extras.ATM, item, "One-Stop-ATM" in facilities)
            apply_yes_no("sells:lottery", item, "One-Stop-Lottery" in facilities)
            apply_yes_no("paypoint", item, "One-Stop-Pay-Point" in facilities)

            item["extras"]["store_format"] = location["location"].get("format", {}).get("storeFormat")
            self.crawler.stats.inc_value(
                f'atp/one_stop_gb/store_format/{location["location"].get("format", {}).get("storeFormat")}'
            )

            yield item
