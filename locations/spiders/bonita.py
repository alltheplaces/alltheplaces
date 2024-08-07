from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_SI, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class BonitaSpider(Spider):
    name = "bonita"
    item_attributes = {"brand": "Bonita", "brand_wikidata": "Q892598"}
    allowed_domains = ["www.bonita.de"]
    start_urls = [
        "https://www.bonita.de/de/de/shop_api/app/store_finder/search.json?country=DE&distance=10000",
        "https://www.bonita.de/de/de/shop_api/app/store_finder/search.json?country=NL&distance=10000",
        "https://www.bonita.de/de/de/shop_api/app/store_finder/search.json?country=AT&distance=10000",
        "https://www.bonita.de/de/de/shop_api/app/store_finder/search.json?country=CH&distance=10000",

    ]

    def parse(self, response):
        for location in response.json()["data"]["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["id"]
            item["name"] = None

            item["street"] =  merge_address_lines([location["address_line_1"], location["address_line_2"]])
            item["opening_hours"] = OpeningHours()
            if location["opening_hours_monday"]:
                item["opening_hours"].add_ranges_from_string("Monday " + location["opening_hours_monday"])
            if location["opening_hours_tuesday"]:
                item["opening_hours"].add_ranges_from_string("Tuesday " + location["opening_hours_tuesday"])
            if location["opening_hours_wednesday"]:
                item["opening_hours"].add_ranges_from_string("Wednesday " + location["opening_hours_wednesday"])
            if location["opening_hours_thursday"]:
                item["opening_hours"].add_ranges_from_string("Thursday " + location["opening_hours_thursday"])
            if location["opening_hours_friday"]:
                item["opening_hours"].add_ranges_from_string("Friday " + location["opening_hours_friday"])
            if location["opening_hours_saturday"]:
                item["opening_hours"].add_ranges_from_string("Saturday " + location["opening_hours_saturday"])
            if location["opening_hours_sunday"]:
                item["opening_hours"].add_ranges_from_string("Sunday " + location["opening_hours_sunday"])

            yield item
