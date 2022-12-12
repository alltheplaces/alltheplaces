import json

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import GeojsonPointItem


class PrimarkGBSpider(SitemapSpider):
    name = "primark_gb"
    item_attributes = {"brand": "Primark", "brand_wikidata": "Q137023"}
    allowed_domains = ["primark.com"]
    sitemap_urls = ["https://www.primark.com/en-gb/sitemap/sitemap-store-locator.xml"]
    sitemap_rules = [(r"https:\/\/www\.primark\.com\/en-gb\/stores\/[-\w]+\/.+$", "parse")]

    def parse(self, response):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())

        store = data["props"]["pageProps"]["storeDetailsPage"]["props"]["storeDetails"]

        item = GeojsonPointItem()
        item["lat"] = store["displayCoordinate"]["latitude"]
        item["lon"] = store["displayCoordinate"]["longitude"]
        item["name"] = " ".join([store["name"], store["geomodifier"]])
        item["street_address"] = ", ".join(filter(None, [store["address"]["line1"], store["address"]["line2"]]))
        item["city"] = store["address"]["city"]
        item["postcode"] = store["address"]["postalCode"]
        item["country"] = store["address"]["countryCode"]
        item["phone"] = store["phoneNumber"]
        item["website"] = response.url
        item["ref"] = store["id"]

        oh = OpeningHours()
        for day in DAYS_FULL:
            if times := store["hours"][day.lower()]["openIntervals"]:
                for time in times:
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
