import json

from scrapy import Request

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class BeaurepairesAUSpider(AmastyStoreLocatorSpider):
    name = "beaurepaires_au"
    item_attributes = {"brand": "Beaurepaires", "brand_wikidata": "Q4877630"}
    allowed_domains = ["www.beaurepaires.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for domain in self.allowed_domains:
            yield Request(url=f"https://{domain}/amlocator/index/ajax/", method="POST", headers={"X-Requested-With": "XMLHttpRequest"})

    def parse_item(self, item, location, popup_html):
        item["street_address"] = item.pop("addr_full")
        oh = OpeningHours()
        schedule = json.loads(location["schedule_string"])
        for day_name, day in schedule.items():
            if day[f"{day_name}_status"] != "1":
                continue
            open_time = day["from"]["hours"] + ":" + day["from"]["minutes"]
            break_start = day["break_from"]["hours"] + ":" + day["break_from"]["minutes"]
            break_end = day["break_to"]["hours"] + ":" + day["break_to"]["minutes"]
            close_time = day["to"]["hours"] + ":" + day["to"]["minutes"]
            if break_start == break_end:
                oh.add_range(day_name.title(), open_time, close_time)
            else:
                oh.add_range(day_name.title(), open_time, break_start)
                oh.add_range(day_name.title(), break_end, close_time)
        item["opening_hours"] = oh.as_opening_hours()

        yield item
