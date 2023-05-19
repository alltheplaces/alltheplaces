import re

import reverse_geocoder
import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class WHSmithGBSpider(scrapy.Spider):
    name = "whsmith_gb"
    item_attributes = {"brand": "WHSmith", "brand_wikidata": "Q1548712", "extras": Categories.SHOP_NEWSAGENT.value}
    allowed_domains = ["whsmith.co.uk"]
    start_urls = [
        "https://www.whsmith.co.uk/mobify/proxy/api/s/whsmith/dw/shop/v21_3/stores?latitude=57.28687230000001&longitude=-2.3815684&distance_unit=mi&max_distance=20012&start=0&count=200"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        # trunk-ignore(gitleaks/generic-api-key)
        "DEFAULT_REQUEST_HEADERS": {"x-dw-client-id": "e67cbaf5-f422-4895-967a-abf461ba92e2"},
    }

    def parse(self, response):
        if not response.json().get("count"):
            return

        for store in response.json()["data"]:
            if not store["store_locator_enabled"]:
                continue

            item = DictParser.parse(store)
            item["city"] = item["city"].strip()
            item["street_address"] = ", ".join(filter(None, [store.get("address1"), store.get("address2")]))
            item["website"] = "https://www.whsmith.co.uk/stores/details/?StoreID=" + item["ref"]
            item["extras"] = {"type": store["_type"]}

            # Some stores have wildly incorrect coordinates for
            # locations as far away as the Indian Ocean. Only
            # add geometry where coordinates existing within
            # the United Kingdom.
            if item.get("geometry") and item["geometry"]["type"] == "Point":
                if result := reverse_geocoder.get((item["geometry"]["coordinates"][0], item["geometry"]["coordinates"][1]), mode=1, verbose=False):
                    if result["cc"] != "GB":
                        item.pop("geometry")

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if not store.get(f"c_openingTimes{day}") or "closed" in store[f"c_openingTimes{day}"].lower():
                    continue
                start_time, end_time = store[f"c_openingTimes{day}"].split("-")
                if ":" not in start_time:
                    if start_time == "24hr":
                        start_time = "00:00"
                    elif len(start_time) == 3:
                        start_time = f"{start_time[0]}:{start_time[1:2]}"
                    elif len(start_time) == 4:
                        start_time = f"{start_time[0:1]}:{start_time[2:3]}"
                if ":" not in end_time:
                    if end_time == "24hr":
                        end_time = "24:00"
                    elif len(end_time) == 3:
                        end_time = f"{end_time[0]}:{end_time[1:2]}"
                    elif len(end_time) == 4:
                        end_time = f"{end_time[0:1]}:{end_time[2:3]}"
                item["opening_hours"].add_range(day, start_time, end_time)

            yield item

        start = int(re.findall(r"start=[0-9]+", response.url)[-1][6:]) + 200
        url = f"https://www.whsmith.co.uk/mobify/proxy/api/s/whsmith/dw/shop/v21_3/stores?latitude=57.28687230000001&longitude=-2.3815684&distance_unit=mi&max_distance=20012&start={start}&count=200"
        yield scrapy.Request(url=url, callback=self.parse)
