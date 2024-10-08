from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines

PIZZA_HUT = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
PIZZA_HUT_DELIVERY = {"brand": "Pizza Hut Delivery", "brand_wikidata": "Q107293079"}


class PizzaHutGBSpider(Spider):
    name = "pizza_hut_gb"
    start_urls = ["https://api.pizzahut.io/v1/huts/?sector=uk-1", "https://api.pizzahut.io/v1/huts/?sector=uk-2"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines(location["address"]["lines"])

            if location["closed"] is True:
                set_closed(item)

            if location["type"] == "restaurant":
                item.update(PIZZA_HUT)
                apply_category(Categories.RESTAURANT, item)
            elif location["type"] == "delivery":
                item.update(PIZZA_HUT_DELIVERY)
                apply_category(Categories.FAST_FOOD, item)

            apply_yes_no(Extras.DELIVERY, item, location["allowedDisposition"]["delivery"])
            apply_yes_no(Extras.TAKEAWAY, item, location["allowedDisposition"]["collection"])

            yield item
