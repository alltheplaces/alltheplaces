import re
from html import unescape

from chompjs import parse_js_object
from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class LillyBGSpider(Spider):
    name = "lilly_bg"
    item_attributes = {"brand": "Lilly", "brand_wikidata": "Q111764460"}
    allowed_domains = ["www.lillydrogerie.bg"]
    start_urls = ["https://www.lillydrogerie.bg/bg/stores"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var locations = {")]/text()').get()
        js_blob = js_blob.split("var locations = ", 1)[1].split("}};", 1)[0] + "}}"
        for location_id, location in parse_js_object(js_blob).items():
            location["latitude"] = location["latitude"].replace(",", "")
            location["longitude"] = location["longitude"].replace(",", "")
            item = DictParser.parse(location)
            item["ref"] = location_id
            desc_html = Selector(text=location["description"])
            item["street_address"] = re.sub(
                r"\s+",
                " ",
                unescape(desc_html.xpath("//p[1]/text()").get("").replace("Адрес:", "").replace("\\xA0", " ")),
            ).strip()
            item["phone"] = unescape(
                desc_html.xpath('//p[contains(text(), "Тел:")]/text()').get("").replace("Тел: +", "")
            )
            hours_string = " ".join(filter(None, desc_html.xpath("//p/text()").getall()))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, DAYS_BG)
            yield item
