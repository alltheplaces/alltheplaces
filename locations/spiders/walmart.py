import json

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class WalmartSpider(CrawlSpider):
    name = "walmart"
    item_attributes = {"brand": "Walmart", "brand_wikidata": "Q483551", "country": "US"}
    allowed_domains = ["walmart.com"]
    download_delay = 5
    start_urls = ["https://www.walmart.com/store/directory"]
    rules = [
        Rule(
            LinkExtractor(
                allow=[
                    r"https:\/\/www\.walmart\.com\/store\/directory\/\w{2}$",
                    r"https:\/\/www\.walmart\.com\/store\/directory\/\w{2}\/[-.\w]+$",
                ]
            )
        ),
        Rule(
            LinkExtractor(allow=r"https:\/\/www\.walmart\.com\/store\/\d+$"),
            callback="parse_store",
        ),
    ]

    def store_hours(self, store):
        if store.get("open24Hours") is True:
            return "24/7"
        elif rules := store.get("operationalHours"):
            oh = OpeningHours()
            for rule in rules:
                if rule.get("closed") is True:
                    continue

                oh.add_range(rule.get("day")[:2], rule.get("start"), rule.get("end"))

            return oh.as_opening_hours()

    def parse_store(self, response):
        script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()

        if script is None:
            return

        data = json.loads(script)

        if data is None:
            return

        store = data["props"]["pageProps"]["initialData"]["initialDataNodeDetail"][
            "data"
        ]["nodeDetail"]

        if store is None:
            return

        item = DictParser.parse(store)

        item["phone"] = store.get("phoneNumber")
        item["name"] = store.get("displayName")
        item["opening_hours"] = self.store_hours(store)

        if addr := store.get("address"):
            item["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        addr.get("addressLineOne"),
                        addr.get("addressLineTwo"),
                    ],
                )
            )
        item["website"] = response.url

        item["extras"] = {}
        item["extras"]["type"] = store.get("type")
        item["extras"]["amenity:fuel"] = any(
            s["name"] == "GAS_STATION" for s in store["services"]
        )

        return item
