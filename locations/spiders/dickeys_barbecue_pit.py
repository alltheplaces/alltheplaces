import json
from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DickeysBarbecuePitSpider(CrawlSpider):
    name = "dickeys_barbecue_pit"
    item_attributes = {"brand": "Dickey's Barbecue Pit", "brand_wikidata": "Q19880747"}
    start_urls = [
        "https://www.dickeys.com/locations",
        "https://www.dickeys.com/ca/en-ca/locations",
    ]
    rules = [
        Rule(
            LinkExtractor(allow=[r"/locations/\w+$", r"/ca/en-ca/locations/\w+$"]),
        ),
        Rule(
            LinkExtractor(allow=[r"/locations/\w+/[A-Za-z-]+$", r"/ca/en-ca/locations/\w+/[A-Za-z-]+$"]),
            callback="parse",
        ),
    ]

    def parse(
        self,
        response: Response,
    ) -> Any:
        raw_data = json.loads(response.xpath('//*[@id="__NEXT_DATA__"]//text()').get())
        yield JsonRequest(
            url=f'https://api-olo-production.dickeys.com/states/{(raw_data["query"]["state"]).title()}/cities/{raw_data["query"]["city"]}/locations',
            callback=self.parse_details,
            headers={"country-alpha-2": "CA" if "/ca/en-ca/" in response.url else "US"},
            cb_kwargs={"website": response.url},
        )

    def parse_details(self, response, **kwargs):
        for location in response.json()["locations"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["ref"] = location["storeCode"]
            item["street_address"] = item.pop("addr_full")
            item["state"] = location["state"]["label"]
            item["website"] = kwargs["website"]
            item["opening_hours"] = OpeningHours()
            for day_time in location["workingHours"]:
                day = day_time["label"]
                open_time = day_time["opened"]
                close_time = day_time["closed"]
                item["opening_hours"].add_range(
                    day=day, open_time=open_time, close_time=close_time, time_format="%I:%M %p"
                )
            yield item
