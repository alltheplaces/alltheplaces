from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class VodacomTZSpider(JSONBlobSpider):
    name = "vodacom_tz"
    item_attributes = item_attributes = {
        "brand": "Vodacom Tanzania",
        "brand_wikidata": "Q7939274",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
    start_urls = ["https://myvodacom.vodacom.co.tz/app/myvodacom/web/vodacom/shop/get-region"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_regions)

    def parse_regions(self, response):
        for region in response.json():
            yield JsonRequest(
                url=f"https://myvodacom.vodacom.co.tz/app/myvodacom/web/vodacom/shop/get-district/{region['regionId']}",
                callback=self.parse_districts,
            )

    def parse_districts(self, response):
        for district in response.json():
            yield JsonRequest(
                url=f"https://myvodacom.vodacom.co.tz/app/myvodacom/web/vodacom/shop/get-store/{district['districtId']}",
                callback=self.parse,
            )

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").replace("Vodashop ", "")
        item["addr_full"] = location.get("location")
        item["phone"] = location["contacts"]
        yield item
