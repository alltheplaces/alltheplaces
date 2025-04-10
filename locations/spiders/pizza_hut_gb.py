from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines

PIZZA_HUT = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
PIZZA_HUT_DELIVERY_INT = {"brand": "Pizza Hut Delivery", "brand_wikidata": "Q191615"}
PIZZA_HUT_DELIVERY_GB = {"brand": "Pizza Hut Delivery", "brand_wikidata": "Q107293079"}


class PizzaHutGBSpider(Spider):
    name = "pizza_hut_gb"
    start_urls = ["https://api.pizzahut.io/v1/huts/?sector=uk-1", "https://api.pizzahut.io/v1/huts/?sector=uk-2"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = merge_address_lines(location["address"]["lines"])

            if location["closed"] is True:
                set_closed(item)

            if location["type"] == "restaurant":
                item.update(PIZZA_HUT)
                apply_category(Categories.RESTAURANT, item)
            elif location["type"] == "delivery" and self.name.endswith("_gb"):
                item.update(PIZZA_HUT_DELIVERY_GB)
                apply_category(Categories.FAST_FOOD, item)
            elif location["type"] == "delivery":
                item.update(PIZZA_HUT_DELIVERY_INT)
                apply_category(Categories.FAST_FOOD, item)

            if location.get("allowedDisposition"):
                apply_yes_no(Extras.DELIVERY, item, location["allowedDisposition"]["delivery"], False)
                apply_yes_no(Extras.TAKEAWAY, item, location["allowedDisposition"]["collection"], False)
            else:
                apply_yes_no(Extras.DELIVERY, item, location["type"] == "delivery")

            yield item
