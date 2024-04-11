from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_SI, OpeningHours


class A1SISpider(Spider):
    name = "a1_si"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q68755"}
    allowed_domains = ["www.a1.si"]
    start_urls = ["https://www.a1.si/pomoc-in-informacije/prodajna-mesta"]

    def parse(self, response):
        locations_js = (
            response.xpath('//script[contains(text(), "var shopBranchList = ")]/text()')
            .get()
            .split("var shopBranchList = ", 1)[1]
            .split("var savedFilters=[];", 1)[0]
        )
        locations = parse_js_object(locations_js)
        for location in locations:
            if location["type"] != 0 and location["type"] != 1:
                continue
            if location["openStatus"] != "open":
                continue
            item = DictParser.parse(location)
            if not location.get("id"):
                # Numerous store IDs are missing. Phone numbers
                # appear to be unique per store so these can be used
                # instead where a store ID is missing.
                item["ref"] = location.get("phone")
            item["name"] = location.get("nameOfShop")
            item["lat"] = location.get("latitude", "").replace(",", ".")
            item["lon"] = location.get("longitude", "").replace(",", ".")
            item["street_address"] = item.pop("addr_full", None)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["workingHours"], days=DAYS_SI)
            apply_category(Categories.SHOP_TELECOMMUNICATION, item)
            yield item
