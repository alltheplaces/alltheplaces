import json
import re
from hashlib import sha1

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_PL, OpeningHours, sanitise_day


class LubaszkaPLSpider(Spider):
    name = "lubaszka_pl"
    item_attributes = {"brand": "Galeria Wypieków Lubaszka", "brand_wikidata": "Q108586693"}
    allowed_domains = ["lubaszka.pl"]
    start_urls = ["https://lubaszka.pl/galerie-wypiekow/"]

    def parse(self, response):
        map_data_js = response.xpath('//script[@id="bakery-places-js-extra"]/text()').get()
        locations = json.loads(re.search(r"var bakeryMapData = ({.*?});", map_data_js, re.DOTALL).group(1))
        for location in locations["locations"]:
            item = DictParser.parse(location)
            item["ref"] = sha1(location["location_name"].encode("UTF-8")).hexdigest()
            item["street_address"] = item.pop("street", None)
            item["opening_hours"] = OpeningHours()
            for day, hours in location["opening_hours"].items():
                day = sanitise_day(day.split("_")[-1], DAYS_PL)
                hours = hours.replace("–", "-")
                if "-" in hours:
                    start_time, end_time = hours.split("-")
                    item["opening_hours"].add_range(day, start_time, end_time)
            if item["phone"] and item["phone"] == "-":
                item.pop("phone")
            yield item
