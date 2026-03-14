import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BjsWholesaleSpider(SitemapSpider):
    name = "bjs_wholesale"
    item_attributes = {"brand": "BJ's Wholesale Club", "brand_wikidata": "Q4835754"}
    allowed_domains = ["bjs.com"]
    sitemap_urls = ["https://www.bjs.com/bjs_ancillary_sitemap.xml"]
    sitemap_rules = [(r"/cl/[-\w]+/\d+", "parse_store")]

    def parse_store(self, response: Response) -> Any:
        store = {}
        json_blob = json.loads(
            response.xpath('//script[@id="bjs-universal-app-state"]/text()')
            .get("")
            .replace("&q;", '"')
            .replace("&s;", "'")
            .replace("&a;", "&")
            .replace("&l;", "<")
            .replace("&g;", ">")
        )
        for key in json_blob:
            if "club/search" in key:
                store = json_blob[key]["Stores"]["PhysicalStore"][0]
                break

        store["ref"] = store.pop("storeName")
        item = DictParser.parse(store)
        item["branch"] = store["Description"][0]["displayStoreName"]
        item["website"] = response.url

        operating_hours = ""
        gas_hours = ""
        store_type = ""
        for attr in store["Attribute"]:
            if attr["name"] == "Hours of Operation":
                operating_hours = attr["value"]
            elif attr["name"] == "StoreType":
                store_type = attr["value"]
            elif attr["name"] == "Gas Hours":
                gas_hours = attr["value"]

        if store_type.lower() == "club":
            item["opening_hours"] = self.parse_hours(operating_hours)
            apply_category(Categories.SHOP_WHOLESALE, item)
        elif store_type.lower() == "gas":
            item["branch"] = item["branch"].removesuffix(" Gas Station")
            item["opening_hours"] = self.parse_hours(gas_hours)
            apply_category(Categories.FUEL_STATION, item)

        yield item

    def parse_hours(self, hours: str) -> OpeningHours:
        opening_hours = OpeningHours()
        opening_hours.add_ranges_from_string(hours.replace(".", ""))
        return opening_hours
