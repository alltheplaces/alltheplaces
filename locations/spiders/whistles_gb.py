from typing import AsyncIterator

from scrapy import Request

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class WhistlesGBSpider(JSONBlobSpider):
    name = "whistles_gb"
    item_attributes = {"brand": "Whistles", "brand_wikidata": "Q7994069"}
    locations_key = "stores"

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in country_iseadgg_centroids(["gb"], 94):
            yield Request(
                f"https://www.whistles.com/on/demandware.store/Sites-WH-UK-Site/en/Stores-FindStores?standaloneStore=on&lat={lat}&long={lon}&dwfrm_address_country=GB"
            )
            yield Request(
                f"https://www.whistles.com/on/demandware.store/Sites-WH-UK-Site/en/Stores-FindStores?concession=on&lat={lat}&long={lon}&dwfrm_address_country=GB"
            )
            yield Request(
                f"https://www.whistles.com/on/demandware.store/Sites-WH-UK-Site/en/Stores-FindStores?lat={lat}&long={lon}&outlet=on&dwfrm_address_country=GB"
            )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["website"] = "https://www.whistles.com" + item["website"]
        item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
        item.pop("facebook", None)
        item.pop("twitter", None)
        apply_category(Categories.SHOP_CLOTHES, item)

        oh = OpeningHours()
        for day in location["workTimes"]:
            if "closed" in day["value"].lower():
                continue
            start, end = day["value"].replace(" ", "").replace("-:", "-").replace(".", ":").split("-")
            oh.add_range(day["weekDay"], start, end)
        item["opening_hours"] = oh
        yield item
