from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours


class SteineckeDESpider(Spider):
    name = "steinecke_de"
    item_attributes = {"brand": "Steinecke", "brand_wikidata": "Q57516278"}
    start_urls = ["https://www.steinecke.info/standorte/"]

    def parse(self, response: Response):
        js_blob = parse_js_object(response.xpath('//script[@id="gmap-locations-js-extra"]/text()').get())
        for store in parse_js_object(js_blob["stores"]):
            store["street_address"] = store.pop("address")
            item = DictParser.parse(store)
            opening_hours = OpeningHours()
            for days, hour_range in store["hours"][0].items():
                opening_hours.add_ranges_from_string(":".join([days, hour_range]), days=DAYS_DE)
            item["opening_hours"] = opening_hours
            yield item
