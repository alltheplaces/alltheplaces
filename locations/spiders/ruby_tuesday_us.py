from scrapy import Spider
from scrapy.http import Response
from chompjs import parse_js_object
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
import re

class RubyTuesdayUsSpider(Spider):
    name = "ruby_tuesday_us"
    item_attributes = {"brand": "Ruby Tuesday", "brand_wikidata": "Q7376400", "nsi_id": "rubytuesday-2fabb0"}
    start_urls = ["https://www.rubytuesday.com/locations/"]

    def parse(self, response: Response):
        scripts = response.css("[type=\"text/javascript\"]::text").getall()
        locations = parse_js_object([s for s in scripts if s.startswith("var locations_meta")][0])
        for location in locations:
            location = location["location"]
            item = DictParser.parse(location['map_pin'])
            item['city'] = item['city'].title()
            item['ref'] = location['branch_id']
            item['branch'] = location['branch_name']
            item['phone'] = location['store_phone_number']
            opening_hours = OpeningHours()
            for day, hour_range in location['opening_hours'].items():
                if 'Closed' in hour_range:
                    continue
                opening_hours.add_range(day, *(re.split(r" - ?", hour_range)), "%I:%M %p")
            item['opening_hours'] = opening_hours
            yield item
