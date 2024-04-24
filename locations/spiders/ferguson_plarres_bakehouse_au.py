import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FergusonPlarresBakehouseAUSpider(Spider):
    name = "ferguson_plarres_bakehouse_au"
    item_attributes = {"brand": "Ferguson Plarre's Bakehouse", "brand_wikidata": "Q5444249"}
    allowed_domains = ["www.fergusonplarre.com.au"]
    start_urls = ["https://www.fergusonplarre.com.au/rest/e/get/locations"]

    def start_requests(self):
        query = {"sort": [{"position": {"order": "asc"}}], "size": 100, "query": {"term": {"status": 1}}}
        for url in self.start_urls:
            yield JsonRequest(url=url, data=query, method="POST")

    def parse(self, response):
        for location in response.json()["hits"]:
            item = DictParser.parse(location["_source"])
            item["addr_full"] = re.sub(r"\s*-\s*This store is located on.*", "", item["addr_full"])
            item["website"] = "https://www.fergusonplarre.com.au/" + location["_source"]["url_key"]
            item["opening_hours"] = OpeningHours()
            for day_name, day in location["_source"]["schedule"].items():
                if not day["status"]:
                    continue
                item["opening_hours"].add_range(day_name.title(), day["from"], day["to"])
            yield item
