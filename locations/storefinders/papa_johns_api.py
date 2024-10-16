from datetime import datetime
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response
from unidecode import unidecode

from locations.categories import PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.papa_johns import PAPA_JOHNS_SHARED_ATTRIBUTES

PAYMENT_OPTIONS_MAP = {
    "apple_pay": PaymentMethods.APPLE_PAY,
    "cash": PaymentMethods.CASH,
    "card": PaymentMethods.CARDS,
    # "bizum" (ES)
    "credit": PaymentMethods.CREDIT_CARDS,
    # "direct_click_to_pay"
    # "fpay" (CL)
    "mercado_pago": PaymentMethods.MERCADO_PAGO,
    # "oneclick" (CL)
    "paypal": PaymentMethods.PAYPAL,
    "sodexo": PaymentMethods.SODEXO,
    # "tenpo" (CL)
    # "web_online" (every location?)
}


class PapaJohnsApiSpider(Spider):
    """
    Paginated JSON response, initial call to something like https://api.new.papajohns.es/v1/stores?latitude=0&longitude=0
    """

    item_attributes = PAPA_JOHNS_SHARED_ATTRIBUTES
    website_base = ""

    def parse(self, response: Response) -> Iterable[Feature]:
        features = response.json().get("page", [])
        for location in features:
            self.pre_process_data(location)
            item = DictParser.parse(location)

            item["branch"] = item.pop("name")

            item["street_address"] = location.get("text_address")
            # commune? is it city or district?
            # also have region
            # and location?

            item["website"] = (
                f"{self.website_base}/{unidecode(location['name'].lower()).replace(' ', '-')}-{item['ref']}"
            )

            if payment_methods := location.get("payment_methods"):
                for method in payment_methods:
                    if tag := PAYMENT_OPTIONS_MAP.get(method):
                        apply_yes_no(tag, item, True)
                    else:
                        self.crawler.stats.inc_value(f"atp/{self.name}/unknown_payment/{method}")

            item["opening_hours"] = self.parse_hours(location, "in_store")
            item["extras"]["opening_hours:delivery"] = self.parse_hours(location, "pj_delivery").as_opening_hours()

            for rule in location["business_hours"]:
                if rule["dispatch_method"] not in ["in_store", "pj_delivery"]:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unknown_hours_type/{rule['dispatch_method']}")

            yield from self.post_process_item(item, response, location) or []

        # n.b. there is "next_page_url" but host was incorrect on the first one found
        if next_page := response.json()["next_page"]:
            yield Request(url=f"{self.start_urls[0]}&page={next_page}")

    def parse_hours(self, location, dispatch_method: str) -> OpeningHours:
        oh = OpeningHours()
        for rule in location["business_hours"]:
            if rule["dispatch_method"] != dispatch_method:
                continue
            oh.add_ranges_from_string(
                rule["day"]
                + " "
                + datetime.strptime(rule["opening_time"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M")
                + " - "
                + datetime.strptime(rule["closing_time"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M")
            )
        return oh

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the data"""

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        """Override with any post processing on the item"""
        yield item
