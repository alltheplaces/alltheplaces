from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule, DetectionResponseRule
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Documentation available at https://developers.woosmap.com/products/search-api/get-started/
#
# To use this spider, supply the API 'key' which typically starts
# with 'woos-' followed by a UUID. Also supply a value for 'origin'
# which is the HTTP 'Origin' header value, typically similar to
# 'https://www.brandname.example'.


class WoosmapSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "woosmap.com"}
    key: str = ""
    origin: str = ""
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/api\.woosmap\.com\/.*?(?<=[?&])key=(?P<key>woos-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(?:&|$)",
            headers='{"origin": .origin}',
        ),
        DetectionResponseRule(
            js_objects={
                "key": r"window.woosmap.public_key",
                "origin": r'window.location.protocol + "//" + window.location.hostname',
            }
        ),
    ]

    def start_requests(self):
        yield JsonRequest(
            url=f"https://api.woosmap.com/stores?key={self.key}&stores_by_page=300&page=1",
            headers={"Origin": self.origin},
            meta={"referrer_policy": "no-referrer"},
        )

    def parse(self, response: Response):
        if features := response.json()["features"]:
            for feature in features:
                item = DictParser.parse(feature["properties"])

                item["street_address"] = ", ".join(filter(None, feature["properties"]["address"]["lines"]))
                item["geometry"] = feature["geometry"]

                item["opening_hours"] = OpeningHours()
                for day, rules in feature["properties"].get("opening_hours", {}).get("usual", {}).items():
                    for hours in rules:
                        if hours.get("all-day"):
                            start = "00:00"
                            end = "24:00"
                        else:
                            start = hours["start"]
                            end = hours["end"]
                        if day == "default":
                            item["opening_hours"].add_days_range(DAYS, start, end)
                        else:
                            item["opening_hours"].add_range(DAYS[int(day) - 1], start, end)

                yield from self.parse_item(item, feature) or []

        if pagination := response.json()["pagination"]:
            if pagination["page"] < pagination["pageCount"]:
                yield JsonRequest(
                    url=f'https://api.woosmap.com/stores?key={self.key}&stores_by_page=300&page={pagination["page"]+1}',
                    headers={"Origin": self.origin},
                    meta={"referrer_policy": "no-referrer"},
                )

    def parse_item(self, item: Feature, feature: dict):
        yield item

    def storefinder_exists(response: Response) -> bool | Request:
        # Example: https://www.auchan.pl/pl/znajdz-sklep
        # This is delivered via Vue.js and is dynamically loading https://webapp.woosmap.com/webapp.js similar to https://codesandbox.io/s/dzgjh
        # if response.xpath('//script[contains(text(), "loadStoreLocator")]').get():
        #     return True

        # TODO: Execute javascript to detect the component?
        # Unclear how to detect from https://www.carrefour.fr/ or https://www.carrefour.fr/magasin/liste#stores-directories-A

        # playwright_page = response.meta["playwright_page"]
        # sitemap = await playwright_page.locator('xpath=//script[contains(@src, "https://webapp.woosmap.com/webapp.js")').all()
        # print(sitemap)
        # if response.xpath('//script[contains(@src, "https://webapp.woosmap.com/webapp.js")]').get():
        #     return True

        if response.xpath('//script[contains(@src, "https://webapp.woosmap.com/webapp.js")]').get():
            return True

        # Example: https://www.decathlon.fr/store-locator
        if response.xpath('//script[contains(text(), "woosmapApiKey")]').get():
            return True

        return False

    def extract_spider_attributes(response: Response) -> dict | Request:
        return {
            "allowed_domains": [urlparse(response.url).netloc],
        }
