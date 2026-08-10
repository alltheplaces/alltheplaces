from typing import Iterable

from parsel import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.lighthouse import LighthouseSpider


class EkoBGSpider(LighthouseSpider):
    name = "eko_bg"
    item_attributes = {"brand": "EKO", "brand_wikidata": "Q111603199"}
    allowed_domains = ["www.eko.bg"]
    start_urls = ["https://www.eko.bg/stations/karta-na-obektite/"]
    requires_proxy = True  # Imperva

    def parse_item(self, item: Feature, location: Selector) -> Iterable[Feature]:
        item["name"] = None
        apply_category(Categories.FUEL_STATION, item)
        yield item
