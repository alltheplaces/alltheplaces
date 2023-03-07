import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KFCAUSpider(scrapy.Spider):
    name = "kfc_au"
    item_attributes = {"brand": "KFC", "brand_wikidata": "Q524757"}
    start_urls = ["https://orderserv-kfc-apac-olo-api.yum.com/dev/v1/stores/"]
    tenant_id = "afd3813afa364270bfd33f0a8d77252d"

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, headers={"x-tenant-id": self.tenant_id})

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            if location["code"] == "1000" or location["code"] == "1001":
                # Ignore dummy stores used for internal testing/development
                continue
            item["ref"] = location["code"]
            item["street_address"] = " ".join(location["localAddress"][0]["address"]["addressLines"])
            item["city"] = location["localAddress"][0]["address"]["city"]
            item["state"] = location["localAddress"][0]["address"]["state"]
            item["country"] = location["localAddress"][0]["address"]["country"]
            item["postcode"] = location["localAddress"][0]["address"]["pinCode"]
            for contact_method in location["contacts"]:
                if contact_method["key"] == "email":
                    item["email"] = contact_method["value"]
                elif contact_method["key"] == "phoneNumber":
                    item["phone"] = contact_method["value"]
            web_path = item["name"].lower().replace(" ", "-") + "/" + item["postcode"]
            item["website"] = "https://www.kfc.com.au/restaurants/" + web_path
            details_url = "https://orderserv-kfc-apac-olo-api.yum.com/dev/v1/stores/details/" + web_path
            yield JsonRequest(
                url=details_url, headers={"x-tenant-id": self.tenant_id}, meta={"item": item}, callback=self.parse_hours
            )

    def parse_hours(self, response):
        item = response.meta["item"]
        trading_days = response.json()["availableTradingHours"]
        oh = OpeningHours()
        for trading_day in trading_days:
            oh.add_range(
                trading_day["dayOfWeek"].title(),
                trading_day["availableHours"]["startTime"],
                trading_day["availableHours"]["endTime"],
                "%H%M",
            )
        item["opening_hours"] = oh.as_opening_hours()
        yield item
