from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.go_review_api import GoReviewApiSpider


class TheFishAndChipCompanyZASpider(GoReviewApiSpider):
    name = "the_fish_and_chip_company_za"
    item_attributes = {"brand": "The Fish & Chip Co", "brand_wikidata": "Q126916268"}
    domain = "fishchipco.localpages.io"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("The Fish & Chip Co ")

        yield item
