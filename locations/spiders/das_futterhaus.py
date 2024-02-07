import re

from chompjs import parse_js_objects
from scrapy import Spider
from scrapy.http import Response

import locations.hours as hours
from locations.dict_parser import DictParser


class DasFutterhausSpider(Spider):
    name = "das_futterhaus"
    item_attributes = {"brand": "Das Futterhaus", "brand_wikidata": "Q1167914"}

    # As of Jan 2024, there are 2 localized versions of the website.
    # Both of them contain the same data (from both countries).
    country_domains = {"AT": "www.dasfutterhaus.at", "DE": "www.futterhaus.de"}

    allowed_domains = list(country_domains.values())

    start_urls = ["https://www.futterhaus.de/service/marktsuche/"]

    hours_pattern = r"^([0-9]{1,2}:[0-9]{2})(?: - | bis )([0-9]{1,2}:[0-9]{2})$"

    def parse(self, response: Response):
        js_data = response.css('script[type="text/javascript"]').get()
        _, locations, *_ = parse_js_objects(js_data)
        for location in locations:
            location = {re.sub(r"^fill?", "", k): v for k, v in location.items()}
            item = DictParser.parse(location)
            item["branch"] = location["Name"]
            item["name"] = self.item_attributes["brand"] + " " + item["branch"]
            item["ref"] = location["Uid"]
            item["street_address"] = location["Strasse"]
            item["city"] = location["Ort"]
            item["postcode"] = location["Plz"]
            opening_hours = hours.OpeningHours()
            try:
                opening_hours.add_days_range(
                    hours.DAYS_WEEKDAY, *(re.findall(self.hours_pattern, location["HoursWeek"].replace(".", ":"))[0])
                )
                opening_hours.add_range(
                    "Sa", *(re.findall(self.hours_pattern, location["HoursSa"].replace(".", ":"))[0])
                )
                item["opening_hours"] = opening_hours
            except:
                pass

            yield item
