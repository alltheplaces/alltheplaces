import json
from copy import deepcopy

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class OxxoMXSpider(Spider):
    name = "oxxo_mx"
    item_attributes = {"brand": "Oxxo", "brand_wikidata": "Q1342538"}
    allowed_domains = ["www.oxxo.com"]
    start_urls = ["https://www.oxxo.com/tiendas"]
    requires_proxy = "MX"

    def parse(self, response):
        js_blob = response.xpath('//store-locator/@*[name()=":raw_stores"]').get()
        for location in parse_js_object(js_blob):
            item = DictParser.parse(location)
            item["ref"] = location["cr"]
            item["website"] = "https://www.oxxo.com/tiendas?cr={}".format(location["cr"])
            item["branch"] = item.pop("name")
            if location.get("start_time") and location.get("end_time"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, location["start_time"], location["end_time"])
            if location.get("categories"):
                categories = json.loads(location["categories"])
                if "oxxogas" in categories:
                    fuel_station_item = deepcopy(item)
                    fuel_station_item["ref"] += "-fuel"
                    apply_category(Categories.FUEL_STATION, fuel_station_item)
                    yield fuel_station_item
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
