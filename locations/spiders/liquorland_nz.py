import re

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LiquorlandNZSpider(Spider):
    name = "liquorland_nz"
    item_attributes = {"brand": "Liquorland", "brand_wikidata": "Q110295342", "extras": Categories.SHOP_ALCOHOL.value}
    allowed_domains = ["www.liquorland.co.nz"]
    start_urls = ["https://www.liquorland.co.nz/store/GetStoreLocationsJsonFileForRegion?regionid=0"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            item = DictParser.parse(location["properties"])
            item["ref"] = location["properties"]["url"].split("?StoreId=", 1)[1]
            item["geometry"] = location["geometry"]
            item["addr_full"] = re.sub(
                r"\s?,(?=[^\s])",
                ", ",
                re.sub(r"\s+", " ", location["properties"]["address"].replace("<br>", ",")).strip(),
            )
            item["website"] = "https://www.liquorland.co.nz" + location["properties"]["url"]
            hours_string = " ".join(
                filter(None, map(str.strip, Selector(text=location["properties"]["hours"]).xpath("//text()").getall()))
            )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
