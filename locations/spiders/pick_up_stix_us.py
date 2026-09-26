from typing import Any, Iterable

import chompjs
from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class PickUpStixUSSpider(JSONBlobSpider):
    name = "pick_up_stix_us"
    item_attributes = {"brand": "Pick Up Stix", "brand_wikidata": "Q7190707"}
    start_urls = ["https://www.pickupstix.com/locations"]

    def extract_json(self, response: Response) -> list[dict]:
        script = response.xpath('//script[contains(text(), "var jsonContent")]/text()').get()
        return chompjs.parse_js_object(script.split("var jsonContent = ", 1)[1])["data"]

    def pre_process_data(self, location: dict) -> None:
        location["street_address"] = merge_address_lines(
            [f'{location["street_number"]} {location["address_route"]}', location.get("subpremise")]
        )
        location["country"] = "US"
        location["website"] = location["url"]

        # The official record has the suite in the city field, while its title and URL identify Dana Point.
        if location.get("unique_id") == "dana-point":
            location["city"] = location["title"]

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        if location.get("active") != "on":
            return

        item["branch"] = item.pop("name", None)

        hours = OpeningHours()
        for line in Selector(text=location["hours"]).xpath("//li/text()").getall():
            hours.add_ranges_from_string(line)
        item["opening_hours"] = hours

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "asian"
        yield item
