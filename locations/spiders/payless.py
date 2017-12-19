import scrapy
from locations.items import GeojsonPointItem
import json
import re
import json

default_headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/63.0.3239.84 Safari/537.36"}


class PaylessSpider(scrapy.Spider):
    name = "payless"
    allowed_domains = ["payless.com"]

    def start_requests(self):
        urls = (
            'https://www.payless.com/on/demandware.store/Sites-payless-Site/default/Stores-GetNearestStores?postalCode'
            '=11230&countryCode=US&distanceUnit=imperial&maxdistance=5000',
        )
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers=default_headers)

    def parse(self, response):
        if response.status == 200:
            stores = json.loads(response.body_as_unicode())
            for store in stores["stores"].values():
                street = "{} {}".format(store["address1"], store["address2"]).strip()
                has_house_number = store["address1"].split(" ")[0].isnumeric()
                website = "https://www.payless.com/on/demandware.store/Sites-payless-Site/default/Stores-Details" \
                          "?StoreID={}".format(
                    store["number"])
                yield GeojsonPointItem(lat=store["latitude"],
                                       lon=store["longitude"],
                                       name=store["name"],
                                       addr_full="{street}, {city}, {stateCode}, {postalCode}".format(street=street,
                                                                                                      **store),
                                       housenumber=store["address1"].split(" ")[0] if has_house_number else None,
                                       street=" ".join(store["address1"].split(" ")[1:]) if has_house_number else store[
                                           "address1"],
                                       city=store["city"],
                                       state=store["stateCode"],
                                       postcode=store["postalCode"],
                                       country=store["countryCode"],
                                       phone=store["phone"],
                                       website=website,
                                       opening_hours=store["storeHours"].replace("<br>", "; ").replace(" :",
                                                                                                       ": ").title(),
                                       ref=store["number"],
                                       )
