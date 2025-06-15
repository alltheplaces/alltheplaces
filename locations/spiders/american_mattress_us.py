from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.amai_promap import AmaiPromapSpider


class AmericanMattressUSSpider(AmaiPromapSpider):
    name = "american_mattress_us"
    start_urls = ["https://www.americanmattress.com/pages/store-locator"]
    item_attributes = {"brand": "American Mattress", "brand_wikidata": "Q126896153"}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BED, item)
        yield item
