import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS_FULL


class WHSmithGB(scrapy.Spider):
    name = "whsmith_uk"
    item_attributes = {"brand": "WHSmith", "brand_wikidata": "Q1548712"}
    allowed_domains = ["whsmith.co.uk"]
    start_urls = [
        "https://www.whsmith.co.uk/mobify/proxy/api/s/whsmith/dw/shop/v21_3/stores?latitude=57.28687230000001&longitude=-2.3815684&distance_unit=mi&max_distance=20000&count=200"
    ]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "x-dw-client-id": "e67cbaf5-f422-4895-967a-abf461ba92e2"
        }
    }
    download_delay = 1  # Requested by robots.txt

    def parse(self, response):
        if next_url := response.json().get("next"):
            yield scrapy.Request(url=next_url)

        for store in response.json()["data"]:
            item = DictParser.parse(store)

            item["street_address"] = ", ".join(
                filter(None, [store.get("address1"), store.get("address2")])
            )

            oh = OpeningHours()
            for day in DAYS_FULL:
                if not store.get("c_openingTimes" + day):
                    continue

                if store["c_openingTimes" + day].lower() == "closed":
                    continue

                start_time, end_time = store["c_openingTimes" + day].split("-")
                if start_time == "24hr":
                    start_time = "00:00"
                if end_time == "24hr":
                    end_time = "24:00"
                oh.add_range(day, start_time, end_time)

            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = (
                "https://www.whsmith.co.uk/stores/details/?StoreID=" + item["ref"]
            )

            yield item
