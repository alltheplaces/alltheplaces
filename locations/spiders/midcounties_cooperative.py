import hashlib

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MidcountiesCooperativeSpider(Spider):
    name = "midcounties_cooperative"
    item_attributes = {
        "brand": "Midcounties Co-operative",
        "brand_wikidata": "Q6841138",
        "country": "GB",
    }
    start_urls = ["https://www.midcounties.coop/static/js/stores.json"]

    def parse(self, response):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)

            if "PO" in item["name"] or "Post Office" in item["name"]:
                # Let's skip post offices for now, hopefully they'll get their own spider
                continue

            item["website"] = store.get("branchLink")

            item["street_address"] = ", ".join(
                filter(
                    None,
                    [store.get("addressLine1"), store.get("addressLine2")],
                )
            )

            oh = OpeningHours()
            for day in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]:
                open_time = store.get(day + "Open")
                close_time = store.get(day + "Close")

                if open_time is None or close_time is None:
                    continue

                if len(open_time) == 4:
                    open_time = "0" + open_time
                if len(close_time) == 4:
                    close_time = "0" + close_time

                open_time = open_time.replace(".", ":")
                close_time = close_time.replace(".", ":")

                oh.add_range(day[:2].title(), open_time, close_time)

            item["opening_hours"] = oh.as_opening_hours()

            item["addr_full"] = ", ".join(
                filter(
                    None,
                    [
                        item["street_address"],
                        item["city"],
                        item["postcode"],
                        "United Kingdom",
                    ],
                )
            )

            # No ref in source, so we'll have to make our own
            item["ref"] = hashlib.sha256(item["addr_full"].encode("utf_8")).hexdigest()

            yield item
