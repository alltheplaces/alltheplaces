from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenSESpider(JSONBlobSpider):
    name = "seven_eleven_se"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = ["https://storage.googleapis.com/public-store-data-prod/stores-seven_eleven.json"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)
        item["street_address"] = merge_address_lines(feature["address"])

        if feature["type"] == "seven_eleven":
            item["branch"] = item.pop("name").removeprefix("7-Eleven ")
        elif feature["type"] == "seven_eleven_express":
            item["branch"] = item.pop("name").removeprefix("7-Eleven Express ")
            item["name"] = "7-Eleven Express"
        else:
            self.logger.error("Unexpected store type: {}".format(feature["type"]))

        item["opening_hours"] = OpeningHours()
        for day_hours in feature["openhours"]["standard"]:
            item["opening_hours"].add_range(DAYS[day_hours["weekday"]], day_hours["hours"][0], day_hours["hours"][1])
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
