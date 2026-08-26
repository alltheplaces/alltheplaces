import re

from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class VpzGBSpider(UberallSpider):
    name = "vpz_gb"
    item_attributes = {"brand": "VPZ", "brand_wikidata": "Q107300487"}
    key = "GTKUBZglSKHUX6xr99T8FQfxPyHfa5"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["image"] = None
        item["ref"] = location.get("id")
        item["website"] = "https://www.vpz.co.uk/stores/l/{0}/{1}/{2}".format(re.sub("[-., '/]+","-",location.get("city").lower()),re.sub("[-., '/]+","-",location.get("streetAndNumber").lower()),location.get("id"))
        apply_category(Categories.SHOP_E_CIGARETTE, item)
        yield item
