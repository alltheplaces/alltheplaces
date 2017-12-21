import scrapy
from locations.items import GeojsonPointItem
import json


class PaylessSpider(scrapy.Spider):
    name = "payless"
    allowed_domains = ["payless.com"]
    start_urls = (
        'https://www.payless.com/on/demandware.store/Sites-payless-Site/default/Stores-GetNearestStores?postalCode'
        '=11230&countryCode=US&distanceUnit=imperial&maxdistance=5000',
    )

    base_url = "https://www.payless.com/on/demandware.store/Sites-payless-Site/default/Stores-Details?StoreID={}"

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())
        for store in stores["stores"].values():
            street = "{} {}".format(store["address1"], store["address2"]).strip()
            has_house_number = store["address1"].split(" ")[0].isnumeric()
            website = self.base_url.format(store["number"])
            point = {
                "lat": store["latitude"],
                "lon": store["longitude"],
                "name": store["name"],
                "addr_full": "{street}, {city}, {stateCode}, {postalCode}".format(street=street, **store),
                "housenumber": store["address1"].split(" ")[0] if has_house_number else None,
                "street": " ".join(store["address1"].split(" ")[1:]) if has_house_number else store["address1"],
                "city": store["city"],
                "state": store["stateCode"],
                "postcode": store["postalCode"],
                "country": store["countryCode"],
                "phone": store["phone"],
                "website": website,
                "opening_hours": store["storeHours"].replace("<br>", "; ").replace(" :", ": ").title(),
                "ref": store["number"],
            }

            yield GeojsonPointItem(**point)
