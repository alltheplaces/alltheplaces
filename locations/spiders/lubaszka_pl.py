from hashlib import sha1

from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours


class LubaszkaPLSpider(Spider):
    name = "lubaszka_pl"
    item_attributes = {"brand": "Galeria Wypieków Lubaszka", "brand_wikidata": "Q108586693"}
    allowed_domains = ["lubaszka.pl"]
    start_urls = ["https://lubaszka.pl/galerie-wypiekow/"]

    def parse(self, response):
        map_data_js = response.xpath('//script[@id="bakery-map-js-extra"]/text()').get()
        locations = parse_js_object("{" + map_data_js.split("{", 1)[1].split("};", 1)[0] + "}")
        for location in locations["locations"]:
            item = DictParser.parse(location)
            item["ref"] = sha1(location["location_name"].encode("UTF-8")).hexdigest()
            item["street_address"] = item.pop("street", None)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS_WEEKDAY, *location["workday_hours"].split(" - ", 1), "%H:%M")
            item["opening_hours"].add_days_range(DAYS_WEEKEND, *location["weekend_hours"].split(" - ", 1), "%H:%M")
            if item["phone"] and item["phone"] == "-":
                item.pop("phone")
            yield item
