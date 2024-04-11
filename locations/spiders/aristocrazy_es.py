from html import unescape

from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AristocrazyESSpider(Spider):
    name = "aristocrazy_es"
    item_attributes = {"brand": "Aristocrazy", "brand_wikidata": "Q117802848"}
    start_urls = [
        "https://www.aristocrazy.com/es/en/Localizador-De-Tiendas?showMap=true&horizontalView=true&isForm=true"
    ]

    def parse(self, response):
        for location in response.xpath("//input/@data-store-info").getall():
            location = parse_js_object(unescape(location))
            item = DictParser.parse(location)
            item["street_address"] = ", ".join(filter(None, [location["address1"], location["address2"]]))
            hours_string = location["storeHours"].replace("Sundays and Holidays from", "Sunday")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
