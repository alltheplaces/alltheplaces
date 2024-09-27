from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingHNSpider(JSONBlobSpider):
    name = "burger_king_hn"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.com1dav1rtual.com/api/em/store/get_filter"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, data={"business_partner": 15})

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("addr_full")
        item["country"] = location["country_name"]
        item["state"] = location["location_one_name"]
        item["city"] = location["location_two_name"]
        yield item
