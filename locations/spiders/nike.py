import datetime
import scrapy
from locations.hours import OpeningHours
from locations.dict_parser import DictParser


class NikeSpider(scrapy.Spider):
    name = "nike"
    item_attributes = {"brand": "Nike", "brand_wikidata": "Q483915"}
    start_urls = [
        "https://storeviews-cdn.risedomain-prod.nikecloud.com/store-locations-static.json"
    ]

    def parse(self, response):
        all_stores = response.json()["stores"]
        for store in all_stores.values():
            store.update(store.get("coordinates"))
            item = DictParser.parse(store)

            days = DictParser.get_nested_key(store, "regularHours")
            opening_hours = OpeningHours()
            for day in days:
                if not days.get(day):
                    continue

                oh = days.get(day)[0]
                opening = oh.get("startTime")
                closing = oh.get("duration")

                closing_h = (
                    closing.split("H")[0].replace("PT", "") if "H" in closing else "0"
                )
                closing_m = (
                    closing[len(closing) - 3 :].replace("M", "")
                    if "M" in closing
                    else "0"
                )

                start = opening.split(":")
                closing_time = str(
                    datetime.timedelta(hours=int(start[0]), minutes=int(start[1]))
                    + datetime.timedelta(hours=int(closing_h), minutes=int(closing_m))
                )
                if "day" in closing_time:
                    closing_time = "00:00"
                else:
                    split_closing_time = closing_time.split(":")
                    closing_time = "".join(
                        split_closing_time[0] + ":" + split_closing_time[1]
                    )

                opening_hours.add_range(day[0:2].title(), opening, closing_time)

            item["opening_hours"] = opening_hours.as_opening_hours()
            item["website"] = "https://www.nike.com/retail/s/" + store["slug"]
            item["image"] = store["imageURL"]
            item["extras"] = {"store_type": store.get("facilityType")}
            yield item
