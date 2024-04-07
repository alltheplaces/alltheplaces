from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class RoddaPaintUSSpider(Spider):
    name = "rodda_paint_us"
    item_attributes = {"brand": "Rodda Paint", "brand_wikidata": "Q7356461", "extras": Categories.SHOP_PAINT.value}
    allowed_domains = ["www.roddapaint.com"]
    start_urls = ["https://www.roddapaint.com/location/"]

    def parse(self, response):
        js_blob = response.xpath('//script[@id="storelocator-script-js-before"]').get()
        js_blob = js_blob.split("bhStoreLocatorLocations = ", 1)[1].split("}]}];", 1)[0] + "}]}]"
        for location in parse_js_object(js_blob):
            if location.get("bh_sl_loc_cat") == "Auth. Dealers":
                continue
            item = DictParser.parse(location)
            item["name"] = item["name"].replace("Rodda Paint – ", "")
            item["street_address"] = merge_address_lines([location.get("address"), location.get("address2")])
            hours_string = " ".join(
                [
                    location.get("hours1"),
                    location.get("hours2"),
                    location.get("hours3"),
                    location.get("hours4"),
                    location.get("hours5"),
                    location.get("hours6"),
                    location.get("hours7"),
                ]
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
