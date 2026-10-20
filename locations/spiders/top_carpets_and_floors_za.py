from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.go_review_api import GoReviewApiSpider


class TopCarpetsAndFloorsZASpider(GoReviewApiSpider):
    name = "top_carpets_and_floors_za"
    item_attributes = {
        "brand": "Top Carpets & Floors",
        "brand_wikidata": "Q120765450",
    }
    domain = "localpages.topcarpetsandfloors.co.za"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["branch"] = item.pop("name").removeprefix("Top Carpets & Floors ")
        item["website"] = "https://localpages.topcarpetsandfloors.co.za/" + feature["slug"]
        apply_category(Categories.SHOP_FLOORING, item)
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//div[contains(@class, "md:hidden")]/div[.//h3]'):
            day = row.xpath("normalize-space(.//h3/text())").get()
            times = row.xpath('normalize-space(.//span[contains(@class, "text-nowrap")])').get()
            if times.lower() == "closed":
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_ranges_from_string(f"{day} {times.replace(' - ', '-')}")
        yield item
