import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.linked_data_parser import LinkedDataParser


# https://restaurants.pizzahut.co.in/sitemap.xml gives lesser count, hence ignored.
class PizzaHutINSpider(Spider):
    name = "pizza_hut_in"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://restaurants.pizzahut.co.in/?page=1"]
    final_page = 0

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not self.final_page:
            self.final_page = int(
                response.xpath(
                    '//button[contains(@class,"mantine-Pagination-control")][@data-with-padding="true"]/text()'
                ).getall()[-1]
            )
        current_page = int(response.xpath('//button[@aria-current="page"]/text()').get())
        linked_data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').get())
        if isinstance(linked_data, list):
            for ld in linked_data:
                if not DictParser.get_nested_key(ld, "itemListElement"):
                    continue
                for item_element in DictParser.get_nested_key(ld, "itemListElement"):
                    if ld_item := item_element.get("item"):
                        item = LinkedDataParser.parse_ld(ld_item)
                        item["ref"] = item["website"] = ld_item["url"].split("?utm_source")[0]
                        apply_category(Categories.RESTAURANT, item)
                        yield item

        if current_page < self.final_page:
            yield response.follow(f"/?page={current_page + 1}")
