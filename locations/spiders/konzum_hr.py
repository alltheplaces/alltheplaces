import re

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_SR, OpeningHours


class KonzumHRSpider(Spider):
    name = "konzum_hr"
    item_attributes = {"brand": "Konzum", "brand_wikidata": "Q518563"}
    start_urls = ["https://trgovine.konzum.hr/api/locations/"]
    address_pattern = r"^\W*(\w.+\w)\W*,\W*(\d{5})\W*(\w.+\w)\W*$"

    def parse(self, response: Response):
        for location in response.json()["locations"]:
            hours_data = parse_js_object(location["work_hours"])
            item = DictParser.parse(location)
            item["street_address"], item["postcode"], item["city"] = re.findall(
                self.address_pattern, item["addr_full"]
            )[0]
            opening_hours = OpeningHours()
            for range in hours_data:
                if not range["from_hour"]:
                    continue
                opening_hours.add_range(
                    DAYS_SR[range["short_name"]], range["from_hour"][-8:-3], range["to_hour"][-8:-3]
                )
            item["opening_hours"] = opening_hours
            if "BENZ" in location["type"]:
                apply_category(Categories.FUEL_STATION, item)
            if any(i != "BENZ" for i in location["type"]):
                apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
