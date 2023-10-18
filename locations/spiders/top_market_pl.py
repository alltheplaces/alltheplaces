import json

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TopMarketPLSpider(Spider):
    name = "top_market_pl"
    item_attributes = {"brand": "Top Market", "brand_wikidata": "Q9360044"}
    start_urls = ["https://www.topmarkety.pl/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1&layout=1"]

    def parse(self, response: Response, **kwargs):
        for shop in response.json():
            item = DictParser.parse(shop)

            del item["website"]

            del item["street"]
            item["street_address"] = shop["street"]

            opening_hours = OpeningHours()
            for day, hours in json.loads(shop["open_hours"]).items():
                if "-" in hours[0]:
                    opening_hours.add_ranges_from_string(f"{day} {hours[0]}")
            item["opening_hours"] = opening_hours

            yield item
