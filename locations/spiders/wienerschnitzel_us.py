import base64
import json
import re
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

FEATURES_EXTRAS_MAP = {
    "drivethru": Extras.DRIVE_THROUGH,
    "walkup": None,
    "tasteefreez": Extras.ICE_CREAM,
    "diningroom": Extras.INDOOR_SEATING,
    "patio": Extras.OUTDOOR_SEATING,
    "breakfast": Extras.BREAKFAST,
    "takeout": Extras.TAKEAWAY,
}


class WienerschnitzelUSSpider(StructuredDataSpider):
    name = "wienerschnitzel_us"
    item_attributes = {"brand_wikidata": "Q324679", "brand": "Wienerschnitzel"}
    allowed_domains = ["www.wienerschnitzel.com"]
    start_urls = ["https://www.wienerschnitzel.com/locations/"]
    wanted_types = ["Restaurant"]
    search_for_email = False
    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Request]:
        for place in json.loads(
            base64.b64decode(re.search(r"window\.wpgmp\.mapdata\d+\s*=\s*\"([^\"]+)\"", response.text).group(1))
        )["places"]:
            yield Request(
                url=place["location"]["redirect_custom_link"],
                callback=self.parse_sd,
                meta={"place": place},
            )

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = response.xpath('//span[@class="ws-store-hero__storeid"]/text()').re_first(r"Store ID:\s*(\S+)")
        item["name"] = None
        item["lat"] = response.meta["place"]["location"]["lat"]
        item["lon"] = response.meta["place"]["location"]["lng"]
        item["addr_full"] = response.meta["place"]["address"]

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//div[@class="location-hours"]//meta[@itemprop="openingHours"]/@content').getall():
            item["opening_hours"].add_ranges_from_string(rule)

        for feature_class in response.xpath('//div[@class="location-features"]/div/@class').getall():
            feature, has = feature_class.split()
            if extra := FEATURES_EXTRAS_MAP[feature]:
                apply_yes_no(extra, item, has == "yes")

        apply_category(Categories.FAST_FOOD, item)

        yield item
