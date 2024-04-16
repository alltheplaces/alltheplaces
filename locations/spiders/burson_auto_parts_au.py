from chompjs import chompjs
from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BursonAutoPartsAU(Spider):
    name = "burson_auto_parts_au"
    item_attributes = {"brand": "Burson Auto Parts", "brand_wikidata": "Q117075930"}
    allowed_domains = ["www.burson.com.au"]
    start_urls = ["https://www.burson.com.au/find-a-store"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}  # Possible anti-bot delay in use

    def parse(self, response):
        raw_js = (
            response.xpath('//script[contains(text(), "var map1 = ")]/text()')
            .get()
            .split('"places":', 1)[1]
            .split('"marker_cluster":', 1)[0]
            .strip()[:-1]
        )
        for location in chompjs.parse_js_object(raw_js):
            item = DictParser.parse(location)
            item["city"] = location["location"]["city"]
            item["state"] = location["location"]["state"]
            item["postcode"] = location["location"]["postal_code"]
            item["phone"] = location["location"]["extra_fields"]["phone"]
            item["email"] = location["location"]["extra_fields"]["email"]
            hours_string = " ".join(
                Selector(text=location["location"]["extra_fields"]["hours"]).xpath("//text()").getall()
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
