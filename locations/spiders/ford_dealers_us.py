import json
import re
from copy import deepcopy

import scrapy
from requests import Response
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.ford import FORD_SHARED_ATTRIBUTES, LINCOLN_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class FordDealersUSSpider(PlaywrightSpider):
    name = "ford_dealers_us"
    start_urls = ["https://www.ford.com/dealerships/"]

    BRAND_MAPPING = {
        "Ford": FORD_SHARED_ATTRIBUTES,
        "Lincoln": LINCOLN_SHARED_ATTRIBUTES,
    }
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs):
        client_id = re.search(r"clientId\":\"([0-9-a-z-]+)\"", response.text).group(1)
        js_path = response.xpath('//*[contains(@src,"clientlibs/skin/")]/@src').get()
        yield scrapy.Request(
            url="https://www.ford.com" + js_path,
            callback=self.parse_state,
            cb_kwargs={"token": client_id},
        )

    def parse_state(self, response: Response, **kwargs):
        state_list = (re.search(r"var\s*\w+\s*=\s*\"(.+)\"\.split\(\";\"\),", response.text).group(1)).split(";")
        for make in self.BRAND_MAPPING:
            for state in state_list:
                yield JsonRequest(
                    url="https://www.ford.com/cxservices/dealer/Dealers.json?make={}&state={}".format(make, state),
                    headers={"Application-id": kwargs["token"]},
                    callback=self.parse_details,
                    cb_kwargs={"brand": make},
                )

    def parse_details(self, response: Response, **kwargs):
        if data := json.loads(response.xpath("//pre/text()").get()).get("Response").get("Dealer"):
            for dealer in data:
                item = DictParser.parse(dealer)
                item["ref"] = f"{dealer.get('PACode')}-{kwargs['brand']}"
                item["street_address"] = dealer.get("Address").get("Street1")
                if item["website"] == "http://DealerOn-null":
                    item.pop("website")
                if brand := self.BRAND_MAPPING[kwargs["brand"]]:
                    item.update(brand)

                # SVO - service only
                # SLS - sales only
                # none of the above - sales and service
                location_type = dealer.get("LocationType")

                if location_type != "SVO":
                    sales_item = self.build_sales_item(item)
                    sales_hours = (dealer.get("SalesHours") or {}).get("Day", [])
                    sales_item["opening_hours"] = self.parse_hours(sales_hours)
                    yield sales_item

                if location_type != "SLS":
                    service_item = self.build_service_item(item)
                    service_hours = (dealer.get("ServiceHours") or {}).get("Day", [])
                    service_item["opening_hours"] = self.parse_hours(service_hours)
                    yield service_item

    def build_sales_item(self, item: Feature) -> Feature:
        sales_item = deepcopy(item)
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item: Feature) -> Feature:
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-SERVICE"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def parse_hours(self, hours: list[dict]) -> OpeningHours | None:
        try:
            oh = OpeningHours()
            for day_time in hours:
                day = day_time["name"]
                if day_time.get("closed"):
                    oh.set_closed(day)
                else:
                    oh.add_range(day=day, open_time=day_time.get("open"), close_time=day_time.get("close"))
            if oh.as_opening_hours():
                return oh
        except Exception as e:
            self.logger.warning("Error parsing {} {}".format(hours, e))
