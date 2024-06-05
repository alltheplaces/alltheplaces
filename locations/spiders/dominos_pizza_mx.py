from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class DominiosMXSpider(Spider):
    name = "dominos_pizza_mx"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            "https://order.golo01.dominos.com/store-locator-international/locate/store?regionCode=MX&latitude=23.634501&longitude=-102.552784",
            headers={"X-DPZ-D": "5267e325-2672-4617-9d60-fcc2b3302811", "DPZ-Market": "MEXICO"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["ref"] = location["StoreID"]
            # TODO: HoursDescription

            apply_yes_no(Extras.DELIVERY, item, location["AllowDeliveryOrders"])
            apply_yes_no(Extras.TAKEAWAY, item, location["AllowCarryoutOrders"])
            for lang, values in (location["LanguageTranslations"] or {}).items():
                item["extras"]["branch:{}".format(lang)] = values["StoreName"]

            yield item
