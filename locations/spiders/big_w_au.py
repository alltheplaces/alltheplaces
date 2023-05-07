import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class BigWAUSpider(scrapy.Spider):
    name = "big_w_au"
    item_attributes = {"brand": "Big W", "brand_wikidata": "Q4906646"}
    allowed_domains = ["www.bigw.com.au"]
    # Any store URL page contains a full JSON blob of store data for all stores.
    start_urls = ["https://www.bigw.com.au/store/0145/BIG-W-Warringah-Mall"]
    # An alltheplaces user agent gets delayed in the hope of causing bots to time out
    # whereas a user agent having the appearance of a user is not delayed.
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get()
        stores = json.loads(data_raw)["props"]["pageProps"]["serializedData"]["store"]
        for store_id, store in stores.items():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["website"] = "https://www.bigw.com.au/store/" + item["ref"] + "/" + item["name"].replace(" ", "-")
            oh = OpeningHours()
            for day, hours in store["tradingHours"][0]["hours"].items():
                if day not in DAYS_EN:
                    continue
                if hours.upper() == "CLOSED":
                    continue
                oh.add_range(day, hours.split(" - ", 1)[0], hours.split(" - ", 1)[1], "%I:%M %p")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
