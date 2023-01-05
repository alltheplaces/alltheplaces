import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class WHSmithGBSpider(scrapy.Spider):
    name = "whsmith_gb"
    item_attributes = {"brand": "WHSmith", "brand_wikidata": "Q1548712", "extras": Categories.SHOP_NEWSAGENT.value}
    allowed_domains = ["whsmith.co.uk"]
    start_urls = [
        "https://www.whsmith.co.uk/mobify/proxy/api/s/whsmith/dw/shop/v21_3/stores?latitude=57.28687230000001&longitude=-2.3815684&distance_unit=mi&max_distance=20000&count=200"
    ]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"x-dw-client-id": "e67cbaf5-f422-4895-967a-abf461ba92e2"}}
    download_delay = 1  # Requested by robots.txt

    def parse(self, response):
        if next_url := response.json().get("next"):
            yield scrapy.Request(url=next_url)

        for store in response.json()["data"]:
            if not store["store_locator_enabled"]:
                continue

            item = DictParser.parse(store)

            item["city"] = item["city"].strip()

            item["street_address"] = ", ".join(filter(None, [store.get("address1"), store.get("address2")]))

            oh = OpeningHours()
            for day in DAYS_FULL:
                if not store.get("c_openingTimes" + day):
                    continue

                if "closed" in store["c_openingTimes" + day].lower():
                    continue

                start_time, end_time = store["c_openingTimes" + day].split("-")
                if start_time == "24hr":
                    start_time = "00:00"
                if end_time == "24hr":
                    end_time = "24:00"
                if ":" not in start_time:
                    start_time += ":00"
                if ":" not in end_time:
                    end_time += ":00"
                oh.add_range(day, start_time, end_time)

            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = "https://www.whsmith.co.uk/stores/details/?StoreID=" + item["ref"]

            item["extras"] = {"type": store["_type"]}

            yield item
