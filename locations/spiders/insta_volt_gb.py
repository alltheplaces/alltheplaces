import re

from scrapy import FormRequest, Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class InstaVoltGBSpider(Spider):
    name = "insta_volt_gb"
    item_attributes = {"brand": "InstaVolt", "brand_wikidata": "Q111173904"}
    start_urls = ["https://instavolt.co.uk/find-electric-vehicle-charge-point-map/"]

    def parse(self, response, **kwargs):
        self.ajax_nonce = re.search(r'"ajax_nonce":"(\w+)"', response.text).group(1)

        yield FormRequest(
            url="https://instavolt.co.uk/wp-json/rouge-location-hub/v1/location-hubs",
            formdata={"security": self.ajax_nonce},
            callback=self.parse_locations,
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)

            item["addr_full"] = location["address_lines_string"]
            item["ref"] = location["alias"]
            item["website"] = f'https://instavolt.co.uk/location-hub/{location["alias"]}'

            apply_yes_no(Extras.TOILETS, item, "facilities^toilet" in location.get("amenities", []))
            apply_yes_no(Extras.WIFI, item, "facilities^free_wifi" in location.get("amenities", []))

            apply_category(Categories.CHARGING_STATION, item)

            yield item
