from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutGBSpider(Spider):
    name = "pizza_hut_gb"
    start_urls = ["https://api.pizzahut.io/v1/huts/?sector=uk-1", "https://api.pizzahut.io/v1/huts/?sector=uk-2"]

    PIZZA_HUT = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    PIZZA_HUT_DELIVERY = {"brand": "Pizza Hut Delivery", "brand_wikidata": "Q107293079"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = merge_address_lines(location["address"]["lines"])

            if location["closed"] is True:
                set_closed(item)

            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs) -> Iterable[Feature]:
        disposition = location.get("allowedDisposition", {})
        # Use allowedDisposition.delivery to distinguish sit-in restaurants from
        # delivery-only outlets — the type field is unreliable across sectors.
        if disposition.get("delivery") is False:
            item.update(self.PIZZA_HUT)
            apply_category(Categories.RESTAURANT, item)
        else:
            item.update(self.PIZZA_HUT_DELIVERY)
            apply_category(Categories.FAST_FOOD, item)

        apply_yes_no(Extras.DELIVERY, item, disposition.get("delivery"))
        apply_yes_no(Extras.TAKEAWAY, item, disposition.get("collection"))
        yield item
