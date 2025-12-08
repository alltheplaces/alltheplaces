from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMNSpider(JSONBlobSpider):
    name = "burger_king_mn"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://delivery-backend-3psaay575a-as.a.run.app/api/v1/client/branch/list"]
    locations_key = "result"

    def post_process_item(self, item, response, location):
        item["branch"] = location["name_mn"]
        item["extras"]["branch:en"] = location["name_en"]
        item["extras"]["branch:mn"] = location["name_mn"]
        item["image"] = location["img"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(
            DAYS, location["open_time"], location["close_time"], time_format="%H:%M:%S"
        )
        yield item
