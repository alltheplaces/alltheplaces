from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class PizzaHutNZSpider(Spider):
    name = "pizza_hut_nz"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    requires_proxy = "US"  # Akamai blocking is in use

    def start_requests(self):
        yield JsonRequest(
            url="https://apiapse2.phdvasia.com/v1/product-hut-fe/localizations?limit=500",
            headers={"Client": "2f28344b-2d60-4754-8985-5c23864a3737"},
        )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]["items"]:
            if not location["active"]:
                continue

            item = DictParser.parse(location)
            item["website"] = "https://www.pizzahut.co.nz/"

            apply_yes_no("sells:alcohol", item, location["alcohol_drinks_available"])
            apply_yes_no(PaymentMethods.CASH, item, location["payment_accepted"]["cash"]["active"])
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, location["payment_accepted"]["credit_card"]["active"])
            apply_category(Categories.RESTAURANT, item)

            yield item
