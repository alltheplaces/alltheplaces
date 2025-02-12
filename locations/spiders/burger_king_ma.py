from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMASpider(JSONBlobSpider):
    name = "burger_king_ma"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://api.solo.skylinedynamics.com/locations?_lat=0&_long=0"]
    locations_key = "data"

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(
                url=url,
                headers={
                    "solo-concept": "KEXdnvC7B21",
                    "accept-language": "fr",
                },
            )

    def post_process_item(self, item, response, location):
        item["branch"] = location["attributes"]["name"].replace("BK ", "")
        item["lat"] = location["attributes"]["lat"]
        item["lon"] = location["attributes"]["long"]
        item["phone"] = location["attributes"]["telephone"]
        item["email"] = location["attributes"]["email"]
        item["addr_full"] = location["attributes"]["line1"]
        item["country"] = location["attributes"]["country"]
        apply_yes_no(Extras.DELIVERY, item, location["attributes"]["delivery-enabled"] == 1, False)
        apply_yes_no(Extras.DRIVE_THROUGH, item, location["attributes"]["is-drive-thru-enabled"], False)
        item["opening_hours"] = OpeningHours()
        if location["attributes"]["open-24-hours"]:
            item["opening_hours"] = "Mo-Su 00:00-24:00"
        else:
            for day in location["attributes"]["opening-hours"]:
                item["opening_hours"].add_range(DAYS[day["day"]], day["open"], day["closed"])

        yield item
