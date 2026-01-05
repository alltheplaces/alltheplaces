from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.subway import SubwaySpider
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SubwaySGSpider(AgileStoreLocatorSpider):
    name = "subway_sg"
    item_attributes = SubwaySpider.item_attributes
    allowed_domains = ["subwayisfresh.com.sg"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"
        item["extras"]["takeaway"] = "yes"
        yield item
