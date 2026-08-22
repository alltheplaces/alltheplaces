from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MoltonBrownSpider(JSONBlobSpider):
    name = "molton_brown"
    item_attributes = {"brand": "Molton Brown", "brand_wikidata": "Q17100584"}
    start_urls = ["https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/37309-rKZWijOqKgXVKbyF/stores.js"]
    locations_key = ["stores"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["tag_ids"] in [["25269"], ["25270"], ["24837"]]:
            item["branch"] = item.pop("name").replace("Molton Brown", "").strip()
            if feature["store_business_hours"]:
                oh = OpeningHours()
                for times in feature["store_business_hours"]:
                    try:
                        if times["open_24hrs"] is not False:
                            oh.add_range(DAYS_FULL[int(times["week_day"]) - 1], "00:00", "23:59")
                        else:
                            if 1 <= times["week_day"] <= len(DAYS_FULL):
                                oh.add_range(
                                    DAYS_FULL[int(times["week_day"]) - 1],
                                    times["open_time"],
                                    times["close_time"],
                                    time_format="%I:%M %p",
                                )
                    except (KeyError, TypeError, ValueError, IndexError):
                        continue
                    item["opening_hours"] = oh
            apply_category(Categories.SHOP_BEAUTY, item)
            yield item
