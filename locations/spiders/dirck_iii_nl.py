from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class DirckIiiNLSpider(JSONBlobSpider):
    name = "dirck_iii_nl"
    item_attributes = {"brand": "Dirck III", "brand_wikidata": "Q109188079"}
    allowed_domains = ["www.dirckiii.nl"]
    start_urls = ["https://www.dirckiii.nl/storelocator/index/ajax/"]
    locations_key = "data"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        if not location.get("is_active"):
            return

        item["ref"] = location.get("storelocator_id")
        item["branch"] = item.pop("name")
        item["email"] = None

        item["street_address"] = clean_address(location.get("address")[1:])

        item["opening_hours"] = OpeningHours()
        if html := location.get("storetime"):
            for row in Selector(text=html).xpath("//p"):
                day = row.xpath('.//span[contains(@class, "day")]/text()').get("").strip()
                time_str = row.xpath('.//span[contains(@class, "open-time")]/text()').get()

                if day in DAYS_NL and time_str and " - " in time_str:
                    open_t, close_t = time_str.split(" - ", 1)
                    item["opening_hours"].add_range(DAYS_NL[day], open_t.strip(), close_t.strip())

        apply_category(Categories.SHOP_ALCOHOL, item)

        yield item
