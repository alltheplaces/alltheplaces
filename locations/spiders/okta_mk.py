from typing import Iterable

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.lighthouse import LighthouseSpider


class OktaMKSpider(LighthouseSpider):
    name = "okta_mk"
    item_attributes = {"brand": "Окта", "brand_wikidata": "Q3350105"}
    allowed_domains = ["www.okta-elpe.com"]
    start_urls = ["https://www.okta-elpe.com/service-stations/find-a-station/"]

    def parse_item(self, item: Feature, location: Selector) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("ОКТА ")

        apply_category(Categories.FUEL_STATION, item)

        yield item
