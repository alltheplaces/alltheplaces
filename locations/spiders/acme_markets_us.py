from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ACMEMarketsUSSpider(Spider):
    name = "acme_markets_us"
    item_attributes = {"brand": "ACME Markets", "brand_wikidata": ""}
    allowed_domains = ["local.acmemarkets.com"]
    start_urls = ["https://local.acmemarkets.com/locator?country=US&storetype=5655"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["response"]["entities"]:
            print(location)
            if location["profile"].get("closed"):
                continue

            item = DictParser.parse(location)
            item["ref"] = location["profile"]["meta"]["id"]
            item["name"] = location["profile"]["name"] + " " + location["profile"]["c_geomodifier"]
            item["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        location["profile"]["address"]["line1"],
                        location["profile"]["address"]["line2"],
                        location["profile"]["address"]["line3"],
                    ],
                )
            )
            item["city"] = location["profile"]["address"]["city"]
            item["state"] = location["profile"]["address"]["region"]
            item["postcode"] = location["profile"]["address"]["postalCode"]
            item["website"] = location["profile"]["websiteUrl"]
            item["phone"] = location["profile"]["mainPhone"]["number"]

            if location["profile"].get("facebookVanityUrl"):
                item["facebook"] = "https://www.facebook.com/" + location["profile"]["facebookVanityUrl"] + "/"
            else:
                item["facebook"] = location["profile"]["facebookPageUrl"]

            item["opening_hours"] = OpeningHours()
            for day_hours in location["profile"]["hours"]["normalHours"]:
                if day_hours["isClosed"]:
                    continue
                for interval in day_hours["intervals"]:
                    item["opening_hours"].add_range(
                        day_hours["day"].title(), str(interval["start"]).zfill(4), str(interval["end"]).zfill(4), "%H%M"
                    )

            apply_yes_no(
                PaymentMethods.AMERICAN_EXPRESS,
                item,
                "American Express" in location["profile"]["paymentOptions"],
                False,
            )
            apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "Google Pay" in location["profile"]["paymentOptions"], False)
            apply_yes_no(PaymentMethods.APPLE_PAY, item, "Apple Pay" in location["profile"]["paymentOptions"], False)
            apply_yes_no(PaymentMethods.CASH, item, "Cash" in location["profile"]["paymentOptions"], False)
            apply_yes_no(PaymentMethods.CHEQUE, item, "Check" in location["profile"]["paymentOptions"], False)
            apply_yes_no(
                PaymentMethods.DINERS_CLUB, item, "Diners Club" in location["profile"]["paymentOptions"], False
            )
            apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "Discover" in location["profile"]["paymentOptions"], False)
            apply_yes_no(PaymentMethods.MASTER_CARD, item, "MasterCard" in location["profile"]["paymentOptions"], False)
            apply_yes_no(
                PaymentMethods.SAMSUNG_PAY, item, "Samsung Pay" in location["profile"]["paymentOptions"], False
            )
            apply_yes_no(PaymentMethods.VISA, item, "Visa" in location["profile"]["paymentOptions"], False)

            apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["profile"]["pickupAndDeliveryServices"], False)

            yield item
