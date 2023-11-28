import json
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import Request

from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class AlbertHeijnSpider(Spider):
    name = "albert_heijn"
    item_attributes = {"brand": "Albert Heijn", "brand_wikidata": "Q1653985"}
    allowed_domains = ["www.ah.nl", "www.ah.be"]
    start_urls = ["https://www.ah.nl/winkels", "https://www.ah.be/winkels"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        request_url = urlparse(response.request.url)
        scripts = response.xpath('//script[contains(text(), "__APOLLO_STATE__")]/text()').extract_first()
        scripts = scripts.split("\n")
        for script in scripts:
            if "__APOLLO_STATE__" in script:
                json_string = script[script.index("=") + 1 :]
                store_ids = json.loads(json_string)["ROOT_QUERY"]['storesSearch({"limit":5000,"start":0})']["result"]
                for item in store_ids:
                    stores_colon_id = item.get("__ref")
                    store_id = stores_colon_id[stores_colon_id.index(":") + 1 :]
                    yield Request(
                        f"https://{request_url.hostname}/winkel/{store_id}",
                        callback=self.parse_store,
                        cb_kwargs={"store_id": store_id},
                    )

    def parse_store(self, response, store_id):
        scripts = response.xpath('//script[contains(text(), "__APOLLO_STATE__")]/text()').extract_first()
        scripts = scripts.split("\n")
        for script in scripts:
            if "__APOLLO_STATE__" in script:
                json_string = script[script.index("=") + 1 :]
                store = json.loads(json_string)[f"Stores:{store_id}"]

                item = Feature()
                item["ref"] = store_id
                item["name"] = "AH"
                item["city"] = store.get("address", {}).get("city")
                item["country"] = store.get("address", {}).get("countryCode")
                item["housenumber"] = store.get("address", {}).get("houseNumber")
                item["postcode"] = store.get("address", {}).get("postalCode")
                item["street"] = store.get("address", {}).get("street")
                item["lat"] = store.get("geoLocation", {}).get("latitude")
                item["lon"] = store.get("geoLocation", {}).get("longitude")
                item["phone"] = store.get("phone")
                self.parse_hours(item, store)

                yield item

    def parse_hours(self, item, store):
        if days_hours := store.get("openingDays"):
            oh = OpeningHours()
            for day_hours in days_hours[0]:  # For some reason it has a 2D list [[{Mo},{Tu},...]]
                if openingHours := day_hours.get("openingHour"):
                    day = DAYS_NL[str(day_hours.get("dayName")).capitalize()]
                    open = openingHours.get("openFrom")
                    close = openingHours.get("openUntil")
                    oh.add_range(day, open, close)
            item["opening_hours"] = oh.as_opening_hours()
