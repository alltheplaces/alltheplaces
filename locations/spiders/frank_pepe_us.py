from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class FrankPepeUSSpider(Spider):
    name = "frank_pepe_us"
    item_attributes = {"brand": "Frank Pepe's", "brand_wikidata": "Q963973"}
    start_urls = ["https://pepe-new-admin.projects.3owl.agency/api/v1/restaurants"]

    BASE_URL = "https://pepespizzeria.com/store/"
    PAYMENT_MAP = {
        "American Express": PaymentMethods.AMERICAN_EXPRESS,
        "Discover": PaymentMethods.DISCOVER_CARD,
        "MasterCard": PaymentMethods.MASTER_CARD,
        "Visa": PaymentMethods.VISA,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["data"]["restaurants"].values():
            for location in region:
                item = DictParser.parse(location)
                item["website"] = urljoin(self.BASE_URL, location["slug"])
                item["branch"] = location["name"].removeprefix("Frank Pepe's of ")
                item["name"] = location["store_name"]
                item["lat"], item["lon"] = location["directions"].split("=", 1)[1].split(",")

                for payment_method in location["supported_card_types"].split("/"):
                    if tag := self.PAYMENT_MAP.get(payment_method):
                        apply_yes_no(tag, item, True)

                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "pizza"

                yield item
