from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BiggbyCoffeeUSSpider(Spider):
    name = "biggby_coffee_us"
    item_attributes = {"brand": "Biggby Coffee", "brand_wikidata": "Q4906876"}
    allowed_domains = ["www.biggby.com"]
    start_urls = ["https://www.biggby.com/locations/"]

    def extract_json(self, response):
        js_blob = response.xpath('//script[contains(text(), "locations: [{")]/text()').get()
        js_blob = "[{" + js_blob.split("locations: [{", 1)[1].split("}]", 1)[0] + "}]"
        return parse_js_object(js_blob)

    def parse(self, response):
        for location in self.extract_json(response):
            if location["acf"]["store_coming_soon"]:
                continue
            item = DictParser.parse(location["acf"])
            item["street_address"] = clean_address([location["acf"]["address_one"], location["acf"]["address_two"]])
            if location["acf"].get("location_map"):
                item["addr_full"] = location["acf"]["location_map"]["address"]
                item["lat"] = location["acf"]["location_map"]["lat"]
                item["lon"] = location["acf"]["location_map"]["lng"]
            if location["acf"].get("monday_thru_thurs_open_hour"):
                item["opening_hours"] = OpeningHours()
                hours_string = (
                    "Mo-Th: "
                    + location["acf"].get("monday_thru_thurs_open_hour", "")
                    + " - "
                    + location["acf"].get("mon_thru_thurs_close_hour", "")
                )
                hours_string = (
                    hours_string
                    + " Fr: "
                    + location["acf"].get("friday_open_hour", "")
                    + " - "
                    + location["acf"].get("friday_close_hour", "")
                )
                hours_string = (
                    hours_string
                    + " Sa: "
                    + location["acf"].get("sat_open_hour", "")
                    + " - "
                    + location["acf"].get("sat_close_hour", "")
                )
                hours_string = (
                    hours_string
                    + " Su: "
                    + location["acf"].get("sun_open_hour", "")
                    + " - "
                    + location["acf"].get("sun_close_hour", "")
                )
                item["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.CAFE, item)
            apply_yes_no(Extras.WIFI, item, location["acf"]["wifi"], False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["acf"]["drive_thru"], False)
            yield item
