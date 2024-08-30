from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class PizzaHutMXSpider(Spider):
    name = "pizza_hut_mx"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    requires_proxy = True

    def start_requests(self):
        yield JsonRequest(
            url="https://apisae1.phdvasia.com/v1/product-hut-fe/localizations?limit=400",
            headers={"Client": "e73194ae-309e-4f8e-81d7-ef95c3179d20"},
        )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]["items"]:
            if not location["active"]:
                continue
            item = DictParser.parse(location)
            apply_yes_no("sells:alcohol", item, location["alcohol_drinks_available"])
            apply_yes_no(PaymentMethods.CASH, item, location["payment_accepted"]["cash"]["active"])
            apply_category(Categories.RESTAURANT, item)
            yield item
