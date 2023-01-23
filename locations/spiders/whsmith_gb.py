import re

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

            oh = OpeningHours()
            for day in DAYS_FULL:
                if not store.get(f"c_openingTimes{day}") or "closed" in store[f"c_openingTimes{day}"].lower():
                    continue

                start_time, end_time = store[f"c_openingTimes{day}"].split("-")
                oh.add_range(
                    day=day,
                    open_time="00:00" if start_time == "24hr" else start_time,
                    close_time="24:00" if end_time == "24hr" else end_time,
                )

            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = "https://www.whsmith.co.uk/stores/details/?StoreID=" + item["ref"]

            item["extras"] = {"type": store["_type"]}

            yield item

        start = int(re.findall(r"start=[0-9]+", response.url)[-1][6:]) + 200
        url = f"https://www.whsmith.co.uk/mobify/proxy/api/s/whsmith/dw/shop/v21_3/stores?latitude=57.28687230000001&longitude=-2.3815684&distance_unit=mi&max_distance=20012&start={start}&count=200"
        yield scrapy.Request(url=url, callback=self.parse)
