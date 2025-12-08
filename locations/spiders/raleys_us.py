from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider

BRAND_MAP = {
    "Bel Air": {"brand": "Bel Air", "brand_wikidata": "Q112922067"},
    "Nob Hill Foods": {"name": "Nob Hill Foods", "brand": "Nob Hill Foods"},
    "Raley's": {"brand": "Raley's", "brand_wikidata": "Q7286970"},
    "Raley's ONE Market": {"name": "Raley's O-N-E Market", "brand": "Raley's", "brand_wikidata": "Q7286970"},
    "Food City": {"brand": "Food City", "brand_wikidata": "Q130253202"},
}

# FoodCityArizonaUSSpider inherits this spider


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
        item["street_address"] = item.pop("street")
        item["ref"] = location["number"]

        item["website"] = response.urljoin(f"/store/{location['number']}")

        if brand := BRAND_MAP.get(location["brand"]["name"]):
            del item["name"]
            item.update(brand)
        else:
            self.logger.error("Unexpected brand: {}".format(location["brand"]["name"]))

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
