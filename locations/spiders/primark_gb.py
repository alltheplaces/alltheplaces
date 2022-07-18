import json
import re

import scrapy

from locations.hours import OpeningHours, DAYS_FULL
from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class PrimarkGBSpider(SitemapSpider):
    name = "primark_gb"
    item_attributes = {"brand": "Primark", "brand_wikidata": "Q137023"}
    allowed_domains = ["primark.com"]
    sitemap_urls = ["https://www.primark.com/en-gb/sitemap/sitemap-store-locator.xml"]
    # sitemap_rules = [        (r"https:\/\/stores\.primark\.com\/[-\w]+\/[-\w]+\/[-\w%']+", "parse")    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"] == "https://www.primark.com/en-gb/undefined/undefined":
                pass
            m = re.match(
                r"https:\/\/www\.primark\.com\/en-gb\/([-\w]+)\/([-\w&;']+)",
                entry["loc"],
            )
            if m:
                entry[
                    "loc"
                ] = f"https://www.primark.com/en-gb/stores/{m.group(1)}/{m.group(2)}"
                yield entry

    def parse(self, response):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())

        store = data["props"]["pageProps"]["storeDetailsPage"]["props"]["storeDetails"]

        item = GeojsonPointItem()
        item["lat"] = store["displayCoordinate"]["latitude"]
        item["lon"] = store["displayCoordinate"]["longitude"]
        item["name"] = " ".join([store["name"], store["geomodifier"]])
        item["street_address"] = ", ".join(
            filter(None, [store["address"]["line1"], store["address"]["line2"]])
        )
        item["city"] = store["address"]["city"]
        item["postcode"] = store["address"]["postalCode"]
        item["country"] = store["address"]["countryCode"]
        item["phone"] = store["phoneNumber"]
        item["website"] = response.url
        item["ref"] = store["id"]

        oh = OpeningHours()
        for day in DAYS_FULL:
            for time in store["hours"][day.lower()]["openIntervals"]:
                oh.add_range(day[:2], time["start"], time["end"])

        item["opening_hours"] = oh.as_opening_hours()

        item["extras"] = {}

        for payment in store["paymentOptions"]:
            if payment == "AMERICANEXPRESS":
                item["extras"]["payment:american_express"] = "yes"
            elif payment == "ANDROIDPAY":
                item["extras"]["payment:google_pay"] = "yes"
            elif payment == "APPLEPAY":
                item["extras"]["payment:apple_pay"] = "yes"
            elif payment == "CASH":
                item["extras"]["payment:cash"] = "yes"
            elif payment == "MAESTRO":
                item["extras"]["payment:maestro"] = "yes"
            elif payment == "MASTERCARD":
                item["extras"]["payment:mastercard"] = "yes"
            elif payment == "VISA":
                item["extras"]["payment:visa"] = "yes"

        yield item
