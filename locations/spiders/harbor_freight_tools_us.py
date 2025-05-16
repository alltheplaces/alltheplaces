import re
from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours, DAYS_WEEKDAY
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HarborFreightToolsUSSpider(JSONBlobSpider):
    name = "harbor_freight_tools_us"
    item_attributes = {"brand": "Harbor Freight Tools", "brand_wikidata": "Q5654601"}
    allowed_domains = ["api.harborfreight.com"]
    start_urls = ['https://api.harborfreight.com/graphql?operationName=FindStoresNearCoordinates&variables={"filter":{"status":"OPEN"},"latitude":0,"longitude":0,"withDistance":true}&extensions={"persistedQuery":{"version":1,"sha256Hash":"3af6e542b419920c44979e2521ef6b73cd998b9089694f1c12f8f3c29edb7eb1"}}']
    locations_key = ["data", "findStoresNearCoordinates", "stores"]
    download_delay = 10  # Aggressive HTTP 403 rate limiting is used, robots.txt wants a delay of 10s

    def start_requests(self) -> Iterable[JsonRequest]:
        # GraphQL query returns results in a 60mi radius.
        for coordinates in country_iseadgg_centroids(["US"], 94):
            graphql_url = self.start_urls[0].replace('"latitude":0,', f'"latitude":{coordinates[0]},').replace('"longitude":0,', f'"longitude":{coordinates[1]},')
            yield JsonRequest(url=graphql_url)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["title"]
        item.pop("name", None)
        item["addr_full"] = feature["address_description"]
        item["street_address"] = feature["address"]
        item["image"] = feature["image"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(DAYS_WEEKDAY, *feature["store_hours_mf"].split("-"), "%I:%M%p")
        item["opening_hours"].add_range("Sa", *feature["store_hours_sat"].split("-"), "%I:%M%p")
        item["opening_hours"].add_range("Su", *feature["store_hours_sun"].split("-"), "%I:%M%p")
        slug = re.sub(r"-+", "-", re.sub(r"\W", "-", feature["address_description"].lower()))
        store_number = feature["store_number"]
        item["website"] = f"https://www.harborfreight.com/storelocator/{slug}?number={store_number}"
        apply_category(Categories.SHOP_HARDWARE, item)
        yield item
