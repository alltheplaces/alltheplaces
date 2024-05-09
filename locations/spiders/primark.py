import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PrimarkSpider(SitemapSpider):
    name = "primark"
    item_attributes = {"brand": "Primark", "brand_wikidata": "Q137023"}
    allowed_domains = ["primark.com"]
    sitemap_urls = ["https://stores.primark.com/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/stores\.primark\.com\/[-\w]+\/[-\w]+\/[-\w%']+", "parse")]

    def parse(self, response):
        json_text = response.xpath('//script[@class="js-map-config"]/text()').get()
        if json_text is None:
            # These stores are "opening soon"
            return
        js = json.loads(json_text)["entities"][0]["profile"]

        opening_hours = OpeningHours()
        for row in js["hours"]["normalHours"]:
            day = row["day"][:2].capitalize()
            for interval in row["intervals"]:
                start_time = "{:02}:{:02}".format(*divmod(interval["start"], 100))
                end_time = "{:02}:{:02}".format(*divmod(interval["end"], 100))
                opening_hours.add_range(day, start_time, end_time)

        properties = {
            "name": js["name"],
            "street_address": clean_address(
                [
                    js["address"]["line1"],
                    js["address"]["line2"],
                    js["address"]["line3"],
                ]
            ),
            "ref": js["meta"]["id"],
            "website": response.url,
            "city": js["address"]["city"],
            "state": js["address"]["region"],
            "postcode": js["address"]["postalCode"],
            "country": js["address"]["countryCode"],
            "opening_hours": opening_hours.as_opening_hours(),
            "phone": js["mainPhone"]["number"],
            "lat": response.xpath('//meta[@itemprop="latitude"]/@content').get(),
            "lon": response.xpath('//meta[@itemprop="longitude"]/@content').get(),
            "facebook": js.get("facebookPageUrl"),
            "extras": {},
        }

        if js.get("paymentOptions"):
            for payment in js["paymentOptions"]:
                if payment == "Google Pay":
                    properties["extras"]["payment:google_pay"] = "yes"
                elif payment == "Apple Pay":
                    properties["extras"]["payment:apple_pay"] = "yes"
                elif payment == "Cash":
                    properties["extras"]["payment:cash"] = "yes"
                elif payment == "MasterCard":
                    properties["extras"]["payment:mastercard"] = "yes"
                elif payment == "Visa":
                    properties["extras"]["payment:visa"] = "yes"
                elif payment == "American Express":
                    properties["extras"]["payment:american_express"] = "yes"
                elif payment == "Maestro":
                    properties["extras"]["payment:maestro"] = "yes"

        if js["name"] == "Penneys":
            properties["brand"] = "Penneys"

        yield Feature(**properties)
