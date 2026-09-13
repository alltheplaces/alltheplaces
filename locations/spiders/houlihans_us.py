from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class HoulihansUSSpider(StructuredDataSpider):
    name = "houlihans_us"
    item_attributes = {"brand": "Houlihan's", "brand_wikidata": "Q5913100"}
    allowed_domains = ["houlihans.com"]
    start_urls = ["https://www.houlihans.com/store-locator/"]
    wanted_types = ["FoodEstablishment"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # The store list is nested as subOrganization entries of the top-level Organization
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            yield from ld_obj.get("subOrganization", [])

    def post_process_item(self, item, response, ld_data, **kwargs) -> Any:
        item["branch"] = item.pop("name")
        item["ref"] = item["website"]
        apply_category(Categories.RESTAURANT, item)
        yield Request(url=item["website"], callback=self.parse_location, meta={"item": item})

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        item = response.meta["item"]
        item["facebook"] = response.xpath(
            '//a[contains(@href, "https://www.facebook.com/")][not(contains(@href, "/houlihans/"))]/@href'
        ).get()
        item["lat"] = response.xpath("//@data-gmaps-lat").get()
        item["lon"] = response.xpath("//@data-gmaps-lng").get()
        yield item
