from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WegmansUSSpider(JSONBlobSpider):
    name = "wegmans_us"
    item_attributes = {"brand": "Wegmans", "brand_wikidata": "Q11288478"}
    allowed_domains = ["www.wegmans.com"]
    start_urls = ["https://www.wegmans.com/api/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Non-existent robots.txt results in HTML page that cannot be parsed

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        if feature["openState"] != "Open":
            return
        item["ref"] = str(feature["storeNumber"])
        item["branch"] = item.pop("name", None)
        item["website"] = "https://www.wegmans.com/stores/" + feature["slug"]
        apply_category(Categories.SHOP_SUPERMARKET, item)
        item["extras"]["start_date"] = feature["openingDate"].split("T", 1)[0]
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_opening_hours)

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        hours_string = response.xpath('//div[contains(@class, "content-block-hours")]/p/text()').get()
        if hours_string:
            hours_string = hours_string.upper().removeprefix("OPEN").strip()
            if hours_string.endswith(", 7 DAYS A WEEK"):
                hours_string = "Mon-Sun: " + hours_string.split(", 7 DAYS A WEEK", 1)[0]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
