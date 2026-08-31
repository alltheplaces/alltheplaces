import json
from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.storefinders.stockinstore import StockInStoreSpider


class AquilaAUSpider(StockInStoreSpider):
    name = "aquila_au"
    item_attributes = {"brand": "Aquila", "brand_wikidata": "Q17985574"}
    api_site_id = "10379"
    api_widget_id = "383"
    api_widget_type = "storelocator"
    api_origin = "https://aquila.com.au"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Request]:
        item["branch"] = item.pop("name")
        if item["branch"].startswith("Myer "):
            item["located_in"] = "Myer"
            item["located_in_wikidata"] = "Q1110323"
            item["branch"] = item["branch"].removeprefix("Myer ")
        if page_url := location.get("store_locator_page_url"):
            item["website"] = "https://aquila.com.au" + page_url
        apply_category(Categories.SHOP_SHOES, item)
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_hours)

    def parse_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        if schema := response.xpath('//script[@id="stockinstore-schema"]/text()').get():
            item["opening_hours"] = LinkedDataParser.parse_opening_hours(json.loads(schema))
        yield item
