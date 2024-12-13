from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider

BRAND_WIKIDATA = {
    "Bel Air": "Q112922067",
    "Nob Hill Foods": "Q121816894",
    "Raley's": "Q7286970",
    "Raley's ONE Market": "Q7286970",
}


class RaleysUSSpider(JSONBlobSpider):
    name = "raleys_us"
    item_attributes = {"extras": Categories.SHOP_SUPERMARKET.value}
    custom_settings = {"DOWNLOAD_TIMEOUT": 55, "ROBOTSTXT_OBEY": False}
    locations_key = ["data"]
    allowed_domains = ["www.raleys.com"]

    def start_requests(self):
        for domain in self.allowed_domains:
            yield JsonRequest(
                f"https://{domain}/api/store", data={"rows": 1000, "searchParameter": {"shippingMethod": "pickup"}}
            )

    def post_process_item(self, item, response, location):
        item["ref"] = location["number"]
        item["website"] = response.urljoin(f"/store/{location['number']}")
        item["brand"] = item["name"] = location["brand"]["name"]
        item["brand_wikidata"] = BRAND_WIKIDATA.get(location["brand"]["name"])
        item["street_address"] = item.pop("street")

        oh = OpeningHours()
        # TODO: Is it safe to assume that all stores are open 7 days?
        oh.add_ranges_from_string(f"Mo-Su {location['storeHours'].removeprefix('Between ')}")
        item["opening_hours"] = oh

        yield item
