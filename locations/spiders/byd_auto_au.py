from chompjs import parse_js_object
from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BYDAutoAUSpider(Spider):
    name = "byd_auto_au"
    item_attributes = {"brand": "BYD Auto", "brand_wikidata": "Q27423"}
    allowed_domains = ["bydautomotive.com.au"]
    start_urls = ["https://bydautomotive.com.au/find-us"]
    requires_proxy = "AU"

    def parse(self, response):
        js_blob = (
            response.xpath('//script[contains(text(), "var designLocationsArr = ")]/text()')
            .get()
            .split("var designLocationsArr = ", 1)[1]
            .split("}];", 1)[0]
            + "}]"
        )
        locations = parse_js_object(js_blob)
        for location in locations:
            if location["mapBadgeStyle"] != "badge-success":
                continue  # Third party authorised repairer, etc.
            elif location["mapBadge"] == "Approved Panel Repairer":
                continue  # Third party authorised repairer.
            if location["mapBadge"] == "Pop-up Experience":
                continue  # Cars in a shopping centre or public space for advertising purposes.

            item = DictParser.parse(location)
            item["ref"] = str(location["designLocationId"])
            item["postcode"] = str(item["postcode"])
            item.pop("phone", None)  # Always a common phone number for the brand, not an individual location.

            hours_text = " ".join(
                filter(None, map(str.strip, Selector(text=location["openHours"]).xpath("//text()").getall()))
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text)

            match location["mapBadge"]:
                case "Experience Centre" | "Flagship Store" | "Megastore" | "Test Drive & Delivery Centre":
                    apply_category(Categories.SHOP_CAR.value, item)
                case "Service & Repair Centre" | "Service Centre":
                    apply_category(Categories.SHOP_CAR_REPAIR.value, item)
                case _:
                    self.logger.error("Unknown location type cannot be parsed: {}".format(location["mapBadge"]))

            yield item
