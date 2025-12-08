from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_NL
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CurvesNLSpider(WPStoreLocatorSpider):
    name = "curves_nl"
    item_attributes = {"brand": "Curves", "brand_wikidata": "Q5196080"}
    allowed_domains = ["curves.nl"]
    days = DAYS_NL

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Curves ")
        item["website"] = response.urljoin(item["website"])

        yield item
