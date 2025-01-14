from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider

BRAND_MAP = {
    "Bel Air": {"brand": "Bel Air", "brand_wikidata": "Q112922067"},
    "Nob Hill Foods": {"name": "Nob Hill Foods", "brand": "Nob Hill Foods", "brand_wikidata": "Q121816894"},
    "Raley's": {"brand": "Raley's", "brand_wikidata": "Q7286970"},
    "Raley's ONE Market": {"name": "Raley's O-N-E Market", "brand": "Raley's", "brand_wikidata": "Q7286970"},
}


class RaleysUSSpider(JSONBlobSpider):
    name = "raleys_us"
    custom_settings = {"DOWNLOAD_TIMEOUT": 55, "ROBOTSTXT_OBEY": False}
    locations_key = ["data"]
    allowed_domains = ["www.raleys.com"]

    def start_requests(self):
        for domain in self.allowed_domains:
            yield Request(f"https://{domain}/stores", callback=self.start_api_request)

    def start_api_request(self, response):
        yield JsonRequest(
            response.urljoin("/api/store"), data={"rows": 1000, "searchParameter": {"shippingMethod": "pickup"}}
        )

    def post_process_item(self, item, response, location):
        item["ref"] = location["number"]
        item["website"] = response.urljoin(f"/store/{location['number']}")
        if brand := BRAND_MAP.get(location["brand"]["name"]):
            item["name"] = None
            item.update(brand)
        else:
            self.logger.error("Unexpected brand: {}".format(location["brand"]["name"]))
        item["street_address"] = item.pop("street")

        oh = OpeningHours()
        # TODO: Is it safe to assume that all stores are open 7 days?
        oh.add_ranges_from_string(f"Mo-Su {location['storeHours'].removeprefix('Between ')}")
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
