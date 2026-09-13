from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class YanceyRentsUSSpider(WPStoreLocatorSpider):
    name = "yancey_rents_us"
    item_attributes = {"brand": "Yancey Rents", "name": "Yancey Rents"}
    allowed_domains = ["www.yanceybros.com"]
    days = DAYS_EN
    requires_proxy = True

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # The store locator covers every Yancey Bros Co division (equipment
        # sales, hydraulics, power systems, bus sales, etc.), and a "rents"
        # category is also applied to some non-Yancey Rents branches that
        # merely also offer rental services, so filter on the branded name.
        if not item["name"].startswith("Yancey Rents"):
            return
        item["branch"] = item["name"].rsplit("–", 1)[-1].strip()
        item["name"] = None
        # The "url" field is usually a Google review short link rather than
        # the branch's own page, so use the permalink for the website field.
        item["website"] = feature.get("permalink") or item["website"]
        apply_category(Categories.SHOP_PLANT_HIRE, item)
        yield item
