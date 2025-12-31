from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.geo import country_iseadgg_centroids
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksZASpider(JSONBlobSpider):
    name = "starbucks_za"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES | {"extras": Categories.COFFEE_SHOP.value}
    locations_key = "data"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self):
        for lat, lon in country_iseadgg_centroids("ZA", 158):
            yield JsonRequest(
                url=f"https://www.starbucks.co.za/api/v2/stores/?filter%5Bcoordinates%5D%5Blatitude%5D={lat}&filter%5Bcoordinates%5D%5Blongitude%5D={lon}&filter%5Bradius%5D=158"
            )

    def pre_process_data(self, location):
        location.update(location.pop("attributes"))

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["website"] = "/".join(
            ["https://www.starbucks.co.za/store-locator", location["storeNumber"], item["branch"].replace(" ", "-")]
        )
        yield item
