import re

from scrapy import Spider
from scrapy.http import JsonRequest
from unidecode import unidecode

from locations.categories import Categories, Extras, PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class PenneysIESpider(Spider):
    name = "penneys_ie"
    item_attributes = {"brand": "Penneys", "brand_wikidata": "Q137023", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["api001-arh.primark.com"]
    start_urls = ["https://api001-arh.primark.com/bff"]
    locale = "en-ie"
    custom_settings = {"ROBOTSTXT_OBEY": False}  # No robots.txt, ignore to avoid errors.

    def start_requests(self):
        yield JsonRequest(
            url="{}?operationName=StoreLocatorPageQuery&variables=%7B%22slug%22%3A%22search%22%2C%22locale%22%3A%22{}%22%2C%22latitude%22%3Anull%2C%22longitude%22%3Anull%2C%22radius%22%3A50%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22bd880c21a82a27e8b192c9416b63916e0a6c5cb66bff446f8bb0a959e8d3157c%22%7D%7D".format(
                self.start_urls[0], self.locale
            ),
            callback=self.parse_cities_list,
        )

    def parse_cities_list(self, response):
        for city in response.json()["data"]["content"]["props"]["cities"]:
            query = """
query StoresInPageQuery($locale: String!, $city: String!) {
  content: storesInPage(locale: $locale) {
    ...storesInPageFields
  }
}
fragment storesInPageFields on StoresInPage {
  props {
    geosearchByCity(locale: $locale, city: $city) {
      count
      stores {
        id
        trial
        brand: name
        branch: geomodifier
        clickAndCollectStore
        address {
          line1
          line2
          city
          postalCode
          countryCode
          region
        }
        hours {
          monday { isClosed openIntervals { start end } }
          tuesday { isClosed openIntervals { start end } }
          wednesday { isClosed openIntervals { start end } }
          thursday { isClosed openIntervals { start end } }
          friday { isClosed openIntervals { start end } }
          saturday { isClosed openIntervals { start end } }
          sunday { isClosed openIntervals { start end } }
        }
        services {
          id
          name
          address {
            line1
            line2
            city
            postalCode
            countryCode
            region
          }
          hours {
            monday { isClosed openIntervals { start end } }
            tuesday { isClosed openIntervals { start end } }
            wednesday { isClosed openIntervals { start end } }
            thursday { isClosed openIntervals { start end } }
            friday { isClosed openIntervals { start end } }
            saturday { isClosed openIntervals { start end } }
            sunday { isClosed openIntervals { start end } }
          }
          url
        }
        additionalHoursText
        phoneNumber
        facilities
        paymentOptions
        displayCoordinate {
          latitude
          longitude
        }
      }
    }
  }
}"""
            data = {
                "operationName": "StoresInPageQuery",
                "query": query,
                "variables": {
                    "locale": self.locale,
                    "city": city["name"].lower(),
                },
            }
            yield JsonRequest(url=self.start_urls[0], data=data, callback=self.parse_locations_of_city)

    def parse_locations_of_city(self, response):
        locations = response.json()["data"]["content"]["props"]["geosearchByCity"]["stores"]
        for location in locations:
            if "COMING SOON" in location["branch"].upper() or "OPENING SOON" in location["branch"].upper():
                continue

            item = DictParser.parse(location)
            item["branch"] = location["branch"]
            item["name"] = "{} {}".format(location["brand"], location["branch"])
            item["street_address"] = clean_address([location["address"]["line1"], location["address"]["line2"]])

            slug = (
                re.sub(r"-+", "-", re.sub(r"[^\w\- ]", "", unidecode(item["city"]).lower()).replace(" ", "-"))
                + "/"
                + re.sub(
                    r"-+",
                    "-",
                    re.sub(r"[^\w\- ]", "", unidecode(location["address"]["line1"]).lower()).replace(" ", "-"),
                )
            )
            item["website"] = "https://www.primark.com/{}/stores/{}".format(self.locale, slug)

            if location.get("hours"):
                item["opening_hours"] = OpeningHours()
                for day_name, day_hours in location.get("hours").items():
                    if day_hours["isClosed"]:
                        continue
                    for interval in day_hours["openIntervals"]:
                        item["opening_hours"].add_range(day_name, interval["start"], interval["end"])

            if location.get("facilities"):
                apply_yes_no(Extras.TOILETS, item, "CUSTOMERTOILETS" in location.get("facilities"), False)
                apply_yes_no(Extras.WIFI, item, "FREE_WIFI_AVAILABLE" in location.get("facilities"), False)
                apply_yes_no(Extras.WHEELCHAIR, item, "WHEELCHAIR_ACCESS" in location.get("facilities"), False)

            if location.get("paymentOptions"):
                apply_yes_no(PaymentMethods.CASH, item, "CASH" in location.get("paymentOptions"), False)
                apply_yes_no(PaymentMethods.MASTER_CARD, item, "MASTERCARD" in location.get("paymentOptions"), False)
                apply_yes_no(PaymentMethods.VISA, item, "VISA" in location.get("paymentOptions"), False)
                apply_yes_no(
                    PaymentMethods.AMERICAN_EXPRESS, item, "AMERICANEXPRESS" in location.get("paymentOptions"), False
                )
                apply_yes_no(PaymentMethods.MAESTRO, item, "MAESTRO" in location.get("paymentOptions"), False)
                apply_yes_no(PaymentMethods.APPLE_PAY, item, "APPLEPAY" in location.get("paymentOptions"), False)
                apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "ANDROIDPAY" in location.get("paymentOptions"), False)

            yield item
