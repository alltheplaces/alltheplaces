import re

from scrapy import FormRequest, Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class InstaVoltGBSpider(Spider):
    name = "insta_volt_gb"
    item_attributes = {"operator": "InstaVolt", "operator_wikidata": "Q111173904"}
    start_urls = ["https://instavolt.co.uk/find-electric-vehicle-charge-point-map/"]

    def parse(self, response, **kwargs):
        self.ajax_nonce = re.search(r'"ajax_nonce":"(\w+)"', response.text).group(1)
        yield FormRequest(
            url="https://instavolt.co.uk/wp-json/instavolt-location/v1/location",
            formdata={"security": self.ajax_nonce},
            callback=self.parse_locations,
        )

    def parse_locations(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = (
                item.pop("name").removeprefix(f'{location["location_id"]} &#8211; ').replace("&#8211;", ",")
            )
            item["name"] = self.item_attributes["brand"]
            item["addr_full"] = clean_address(location["address_lines"])
            item["ref"] = location["location_id"]
            item["website"] = location["permalink"]
            extras_list = [extras["name"] for extras in location["amenities"]]
            apply_yes_no(Extras.WIFI, item, True if "Free WIFI" in extras_list else False)
            apply_yes_no(Extras.TOILETS, item, True if "Toilet" in extras_list else False)
            apply_category(Categories.CHARGING_STATION, item)
            yield item
