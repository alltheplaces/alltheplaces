from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TheAFLStoreAUSpider(Spider):
    name = "the_afl_store_au"
    item_attributes = {"brand": "The AFL Store", "brand_wikidata": "Q117851311"}
    allowed_domains = ["www.theaflstore.com.au"]
    start_urls = [
        "https://search-developer-toolkit-3loaafdn4dugiezkplh33pnacq.ap-southeast-2.es.amazonaws.com/the-afl-store-au-location/document/_search"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["hits"]["hits"]:
            data = location["_source"]
            item = DictParser.parse(data)
            item["street_address"] = ", ".join(filter(None, [data.get("address1"), data.get("address2")]))
            item["website"] = "https://www.theaflstore.com.au/pages/store?location=" + item["ref"]
            hours_string = ""
            for day_ranges in data["openHours"]:
                start_day = DAYS[day_ranges["dayStart"] - 1]
                end_day = DAYS[day_ranges["dayEnd"] - 1]
                start_time = day_ranges["timeStart"]
                end_time = day_ranges["timeEnd"]
                hours_string = f"{hours_string} {start_day}-{end_day}: {start_time}-{end_time}"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
