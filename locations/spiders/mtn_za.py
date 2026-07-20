from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.go_review_api import GoReviewApiSpider


class MtnZASpider(GoReviewApiSpider):
    name = "mtn_za"
    item_attributes = {"brand": "MTN", "brand_wikidata": "Q1813361"}
    domain = "stores.mtn.co.za"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["branch"] = item.pop("name").removeprefix("MTN ")
        item["website"] = "https://stores.mtn.co.za/" + feature["slug"]
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        hours_string = " ".join(response.xpath('//div[contains(@class, "operating-hours")]//text()').getall())
        hours_string = hours_string.replace("|", "-").replace("day ", ":")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
