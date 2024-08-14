import scrapy
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcAUSpider(scrapy.Spider):
    name = "kfc_au"
    item_attributes = KFC_SHARED_ATTRIBUTES
    region_code = "apac"
    tenant_id = "afd3813afa364270bfd33f0a8d77252d"
    web_root = "https://www.kfc.com.au/restaurants/"
    requires_proxy = True  # Requires AU proxy, possibly residential IPs only.

    def start_requests(self):
        yield JsonRequest(
            url="https://orderserv-kfc-" + self.region_code + "-olo-api.yum.com/dev/v1/stores/",
            headers={"x-tenant-id": self.tenant_id},
        )

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            if location["code"] == "1000" or location["code"] == "1001":
                # Ignore dummy stores used for internal testing/development
                continue
            item["ref"] = location["code"]
            item["street_address"] = clean_address(location["localAddress"][0]["address"]["addressLines"])
            item["city"] = location["localAddress"][0]["address"]["city"]
            item["state"] = location["localAddress"][0]["address"]["state"]
            item["country"] = location["localAddress"][0]["address"]["country"]
            item["postcode"] = location["localAddress"][0]["address"]["pinCode"]
            for contact_method in location["contacts"]:
                if contact_method["key"] == "email":
                    item["email"] = contact_method["value"]
                elif contact_method["key"] == "phoneNumber":
                    item["phone"] = contact_method["value"]
            for channel in location["channelWiseServices"]:
                if channel["channel"] == "web":
                    apply_yes_no(Extras.DELIVERY, item, "delivery" in channel["services"], False)
                    break
            web_path = item["name"].lower().replace(" ", "-") + "/" + item["postcode"]
            if self.web_root:
                item["website"] = self.web_root + web_path
            details_url = (
                "https://orderserv-kfc-" + self.region_code + "-olo-api.yum.com/dev/v1/stores/details/" + web_path
            )
            yield JsonRequest(
                url=details_url, headers={"x-tenant-id": self.tenant_id}, meta={"item": item}, callback=self.parse_hours
            )

    def parse_hours(self, response):
        item = response.meta["item"]
        trading_days = response.json()["availableTradingHours"]
        item["opening_hours"] = OpeningHours()
        for trading_day in trading_days:
            item["opening_hours"].add_range(
                trading_day["dayOfWeek"].title(),
                trading_day["availableHours"]["startTime"],
                trading_day["availableHours"]["endTime"],
                "%H%M",
            )
        yield item
