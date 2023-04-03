import re

from chompjs import chompjs
from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class FantasticFurnitureAUSpider(Spider):
    name = "fantastic_furniture_au"
    item_attributes = {"brand": "Fantastic Furniture", "brand_wikidata": "Q18164803"}
    allowed_domains = ["www.fantasticfurniture.com.au"]
    start_urls = ["https://www.fantasticfurniture.com.au/store-finder"]

    def parse(self, response):
        raw_js = response.xpath('//div[@id="wrapper"]/div/div/script[5]').get()
        js_dicts = list(map(lambda x: x.split("};", 1)[0].strip() + "}", raw_js.split("var store = ")[1:]))
        js_dicts.pop()
        for js_dict in js_dicts:
            js_dict = re.sub(r"'\+(\d+)\+'", r"\1", js_dict)
            location = chompjs.parse_js_object(js_dict)
            item = DictParser.parse(location)
            tooltip_html = Selector(text=location["contentString"])
            item["street_address"] = " ".join(
                tooltip_html.xpath('//div[contains(@class, "store_details")]/p[not(@class)]/text()').getall()
            )
            item["city"] = location["name"]
            item["phone"] = (
                tooltip_html.xpath('//div[contains(@class, "store_details")]/p[contains(@class, "phone")]/text()')
                .get()
                .strip()
            )
            item["website"] = (
                "https://www.fantasticfurniture.com.au"
                + tooltip_html.xpath('//div[contains(@class, "store_details")]/h2/a/@href').get()
            )
            item["opening_hours"] = OpeningHours()
            hours_raw = (
                " ".join(
                    tooltip_html.xpath(
                        '//div[contains(@class, "trading_hours")]/ul/li/*[self::strong or self::small]/text()'
                    ).getall()
                )
                .upper()
                .replace(" - ", " ")
                .replace(" AM", "AM")
                .replace(" PM", "PM")
                .replace("CLOSED", "0:00AM 0:00AM")
                .split(" ")
            )
            hours_raw = [hours_raw[n : n + 3] for n in range(0, len(hours_raw), 3)]
            for day in hours_raw:
                if day[1] == "0:00AM" and day[2] == "0:00AM":
                    continue
                item["opening_hours"].add_range(day[0], day[1], day[2], "%I:%M%p")
            yield item
