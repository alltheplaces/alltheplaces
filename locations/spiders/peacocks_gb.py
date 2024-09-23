import re

from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PeacocksGBSpider(Spider):
    name = "peacocks_gb"
    item_attributes = {"brand": "Peacocks", "brand_wikidata": "Q7157762"}
    start_urls = [
        "https://www.peacocks.co.uk/on/demandware.store/Sites-peacocks-Site/default/Stores-FindStores?radius=1000&lat=51.5072178&long=-0.1275862",
    ]

    def parse(self, response, **kwargs):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["website"] = store["storeDetailsURL"]
            item["branch"] = item.pop("name").removeprefix("PEACOCKS ")

            item["opening_hours"] = OpeningHours()
            data = Selector(text=store["storeHours"])
            for day_time in data.xpath(r'//*[@class = "store-hours"]//tr'):
                day = day_time.xpath("./td[1]/text()").get().replace(":", "")
                time = day_time.xpath(".//td[2]/text()").get().replace(".", ":")
                if time in ["CLOSED", ""]:
                    continue
                open_time, close_time = re.search(r"(\d+:\d+\w+).*(\d+:\d+\w+)", time).groups()
                item["opening_hours"].add_range(
                    day=day, open_time=open_time, close_time=close_time, time_format="%I:%M%p"
                )

            yield item
