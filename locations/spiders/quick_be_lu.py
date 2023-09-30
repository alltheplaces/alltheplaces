from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class QuickBELUSpider(Spider):
    name = "quick_be_lu"
    item_attributes = {"brand": "Quick", "brand_wikidata": "Q286494"}
    allowed_domains = ["www.quick.be"]
    start_urls = ["https://www.quick.be/fr/restaurants"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.find_json_file)

    def find_json_file(self, response):
        build_id = (
            response.xpath('//script[contains(@src, "/_buildManifest.js")]/@src')
            .get()
            .replace("/_next/static/", "")
            .replace("/_buildManifest.js", "")
        )
        yield JsonRequest(f"https://www.quick.be/_next/data/{build_id}/fr/restaurants.json")

    def parse(self, response):
        for location in response.json()["pageProps"]["restaurants"]:
            item = DictParser.parse(location)
            item["lat"] = location["latlng"]["lat"]
            item["lon"] = location["latlng"]["lng"]
            item["street_address"] = item.pop("addr_full")
            item["country"] = "BE"
            if location["country_luxembourg"]:
                item["country"] = "LU"
            item["website"] = "https://www.quick.be/fr/restaurant/" + location["slug"]
            item["opening_hours"] = OpeningHours()
            for day in location["opening_hours"]:
                if day["opening_type"] != 1:
                    continue
                item["opening_hours"].add_range(
                    DAYS[day["weekday_from"] - 1], day["from_hour"], day["to_hour"], "%H:%M:%S"
                )

            if postcode := item.get("postcode"):
                item["postcode"] = str(postcode)

            yield item
