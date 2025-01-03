from json import loads
from typing import Iterable

from scrapy import Request, Selector

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class DunlopSuperDealerAUSpider(AmastyStoreLocatorSpider):
    name = "dunlop_super_dealer_au"
    item_attributes = {
        "brand": "Dunlop Super Dealer",
        "brand_wikidata": "Q131625949",
        "extras": Categories.SHOP_TYRES.value,
    }
    allowed_domains = ["www.dunlopsuperdealer.com.au"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        for domain in self.allowed_domains:
            yield Request(
                url=f"https://{domain}/amlocator/index/ajax/",
                method="POST",
                headers={"X-Requested-With": "XMLHttpRequest"},
            )

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        if not item["name"].startswith("Dunlop Super Dealer "):
            return

        item["street_address"] = item.pop("addr_full")

        match feature["state"]:
            case "569":
                item["state"] = "ACT"
            case "570":
                item["state"] = "NSW"
            case "571":
                item["state"] = "VIC"
            case "572":
                item["state"] = "QLD"
            case "573":
                item["state"] = "SA"
            case "574":
                item["state"] = "TAS"
            case "575":
                item["state"] = "WA"
            case "576":
                item["state"] = "NT"
            case _:
                item["state"] = None

        item["opening_hours"] = OpeningHours()
        if feature.get("schedule_string"):
            schedule = loads(feature["schedule_string"])
            for day_name, day in schedule.items():
                if day[f"{day_name}_status"] != "1":
                    continue
                open_time = day["from"]["hours"] + ":" + day["from"]["minutes"]
                break_start = day["break_from"]["hours"] + ":" + day["break_from"]["minutes"]
                break_end = day["break_to"]["hours"] + ":" + day["break_to"]["minutes"]
                close_time = day["to"]["hours"] + ":" + day["to"]["minutes"]
                if break_start == break_end:
                    item["opening_hours"].add_range(day_name.title(), open_time, close_time)
                else:
                    item["opening_hours"].add_range(day_name.title(), open_time, break_start)
                    item["opening_hours"].add_range(day_name.title(), break_end, close_time)

        yield item
