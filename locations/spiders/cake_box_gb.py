import re
from typing import Iterable

from scrapy import Selector

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class CakeBoxGBSpider(AmastyStoreLocatorSpider):
    name = "cake_box_gb"
    item_attributes = {"brand": "Cake Box", "brand_wikidata": "Q110057905"}
    allowed_domains = ["www.cakebox.com"]

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Cake Box ")
        sel = feature["popup_html"]
        item["city"] = re.search(r"(?<=City: )[^<]+", sel).group(0)
        item["street_address"] = re.search(r"(?<=Address: )[^<]+", sel).group(0)
        item["postcode"] = re.search(r"(?<=Zip: )[^<]+", sel).group(0)
        yield item
