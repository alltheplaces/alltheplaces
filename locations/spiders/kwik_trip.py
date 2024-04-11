from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines

BRANDS = {
    "KWIK SPIRITS": {"name": "Kwik Spirits"},
    "KWIK STAR": {"name": "Kwik Star", "brand": "Kwik Star", "brand_wikidata": "Q123269534"},
    "KWIK TRIP": {"name": "Kwik Trip"},
    "STOP N GO": {"name": "Stop N Go"},
    "TOBACCO OUTLET PLUS": {"name": "Tobacco Outlet Plus"},
    "TOBACCO OUTLET PLUS GROCERY": {"name": "Tobacco Outlet Plus Grocery"},
}


class KwikTripSpider(scrapy.Spider):
    name = "kwiktrip"
    item_attributes = {"brand": "Kwik Trip", "brand_wikidata": "Q6450420"}
    allowed_domains = ["www.kwiktrip.com"]
    start_urls = ["https://www.kwiktrip.com/Maps-Downloads/Store-List"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("(//tr)[position()>1]"):
            yield JsonRequest(
                url="https://www.kwiktrip.com/locproxy.php?location={}".format(
                    location.xpath('.//td[@class="column-1"]/text()').get()
                ),
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()
        item = DictParser.parse(location)
        item["street_address"] = merge_address_lines([location["address"]["address1"], location["address"]["address2"]])

        item["lat"] = location["address"]["latitude"]
        item["lon"] = location["address"]["longitude"]
        item["website"] = "https://www.kwiktrip.com/locator/store?id={}".format(item["ref"])

        if location["open24Hours"]:
            item["opening_hours"] = "24/7"
        else:
            item["opening_hours"] = OpeningHours()
            for rule in location["hours"]:
                item["opening_hours"].add_range(rule["dayOfWeek"], rule["openTime"], rule["closeTime"], "%H:%M:%S")

        properties = [p["displayName"] if p["hasProperty"] else None for p in location["properties"]]

        apply_yes_no(Extras.ATM, item, "ATM" in properties)
        apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in properties)
        apply_yes_no(Extras.SHOWERS, item, "Showers" in properties)
        # "Fleet Cards Accepted"

        apply_yes_no(Fuel.BIODIESEL, item, "Bio Diesel" in properties)
        apply_yes_no(Fuel.CNG, item, "CNG" in properties)
        apply_yes_no(Fuel.DIESEL, item, "Diesel" in properties)
        apply_yes_no(Fuel.E85, item, "E-85" in properties)
        apply_yes_no(Fuel.E88, item, "E-88" in properties)
        # "Diesel Exhaust Fluid", "Gas"

        # TODO: fuel prices

        store_format, _ = item["name"].split(" #", 1)
        if store_format in BRANDS:
            item.update(BRANDS[store_format])

        if location.get("fuel"):
            apply_category(Categories.FUEL_STATION, item)
        else:
            if item["name"] == "Tobacco Outlet Plus":
                apply_category(Categories.SHOP_TOBACCO, item)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
