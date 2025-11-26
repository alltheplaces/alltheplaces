import ast
import re

import scrapy
from requests import Response
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class FordDealersUSSpider(scrapy.Spider):
    name = "ford_dealers_us"
    item_attributes = {
        "brand": "Ford",
        "brand_wikidata": "Q44294",
    }
    start_urls = ["https://www.ford.com/dealerships/"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs):
        client_id = re.search(r"clientId\":\"([0-9-a-z-]+)\"", response.text).group(1)
        yield scrapy.Request(
            url="https://www.ford.com/etc/designs/brand_ford/brand/skin/ford.min.js",
            callback=self.parse_state,
            cb_kwargs={"token": client_id},
        )

    def parse_state(self, response, **kwargs):
        state_list = ast.literal_eval(re.search(r"fullStateNames\s*=\s*(\[.*\]);", response.text).group(1))
        for state in state_list:
            yield JsonRequest(
                url="https://www.ford.com/cxservices/dealer/Dealers.json?make=Ford&state={}".format(state),
                headers={"Application-id": kwargs["token"]},
                callback=self.parse_details,
            )

    def parse_details(self, response):
        if data := response.json().get("Response").get("Dealer"):
            for dealer in data:
                item = DictParser.parse(dealer)
                item["ref"] = dealer.get("PACode")
                item["street_address"] = dealer.get("Address").get("Street1")
                if item["website"] == "http://DealerOn-null":
                    item.pop("website")
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no(Extras.CAR_REPAIR, item, True if dealer.get("serviceAppointmentURL") else False)
                oh = OpeningHours()
                if dealer.get("SalesHours"):
                    for day_time in dealer["SalesHours"]["Day"]:
                        day = day_time["name"]
                        if day_time.get("closed"):
                            oh.set_closed(day)
                        else:
                            oh.add_range(day=day, open_time=day_time.get("open"), close_time=day_time.get("close"))
                item["opening_hours"] = oh
                yield item
