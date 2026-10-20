import json
from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS


class BricksAndMinifigsSpider(JSONBlobSpider, CamoufoxSpider):
    name = "bricks_and_minifigs"
    item_attributes = {"brand": "Bricks & Minifigs", "brand_wikidata": "Q109329121"}
    start_urls = ["https://bricksandminifigs.com/store-locator/"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    def extract_json(self, response: TextResponse) -> list[dict]:
        locations = json.loads(
            response.xpath('//section[@data-interaction="locationsMapSearch"]/@data-locations').get()
        )
        return [location | location.pop("address") for location in locations]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["coming-soon"] == "true":
            return

        title = Selector(text=item.pop("name")).xpath("string()").get()
        item["branch"] = title.split(",")[0].split(" | ")[0].removeprefix("Bricks & Minifigs ")
        item["street_address"] = merge_address_lines([feature["street1"], feature["street2"]])
        item["lat"], item["lon"] = feature["latlong"].split(",")
        item["website"] = response.urljoin(feature["url"])
        oh = OpeningHours()
        oh.add_ranges_from_string(feature["hours"].replace("<br>", " "))
        if not any(
            close_time < open_time or open_time.tm_hour == 0
            for ranges in oh.day_hours.values()
            for open_time, close_time in ranges
        ):
            item["opening_hours"] = oh
        apply_category(Categories.SHOP_TOYS, item)
        yield item
