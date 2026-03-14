from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.aheadworks import AheadworksSpider


class AnimatesNZSpider(AheadworksSpider):
    name = "animates_nz"
    allowed_domains = ["www.animates.co.nz"]
    start_urls = ["https://www.animates.co.nz/store-finder"]
    item_attributes = {"brand": "Animates", "brand_wikidata": "Q110299350"}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_PET, item)
        yield item
