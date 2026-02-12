from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class DayLewisGBSpider(AgileStoreLocatorSpider):
    name = "day_lewis_gb"
    item_attributes = {"brand": "Day Lewis Pharmacy", "brand_wikidata": "Q62563772"}
    allowed_domains = ["daylewis.co.uk"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = f'https://www.daylewis.co.uk/pharmacy-page/{feature["slug"]}'
        yield item
