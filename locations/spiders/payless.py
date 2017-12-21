import scrapy
from locations.items import GeojsonPointItem
import json

def process_hours(hours_str):
    days = hours_str.split("; ")
    out = []
    for day in days:
        if day:
            prefix, hours = day.split(" ")
            start, end = hours.split("-")
            start_hours, start_minutes = int(start[:2]), int(start[2:])
            end_hours, end_minutes = int(end[:2]), int(end[2:])
            end_hours += 12
            formatted = "%s %02d:%02d-%02d:%02d" % (prefix, start_hours, start_minutes, end_hours, end_minutes)
            out.append(formatted)
    return "; ".join(out)


class PaylessSpider(scrapy.Spider):
    name = "payless"
    allowed_domains = ["payless.com"]
    base_url = "https://www.payless.com/on/demandware.store/Sites-payless-Site/default/Stores-Details?StoreID={}"

    def start_requests(self):
        urls = (
            'https://www.payless.com/on/demandware.store/Sites-payless-Site/default/Stores-GetNearestStores?postalCode'
            '=11230&countryCode=US&distanceUnit=imperial&maxdistance=5000',
        )
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())
        for store in stores["stores"].values():
            street = "{} {}".format(store["address1"], store["address2"]).strip()
            has_house_number = store["address1"].split(" ")[0].isnumeric()
            website = self.base_url.format(store["number"])
            point = {}

            point["lat"] = store["latitude"]
            point["lon"] = store["longitude"]
            point["name"] = store["name"]
            point["addr_full"] = "{street}, {city}, {stateCode}, {postalCode}".format(street=street, **store)
            point["housenumber"] = store["address1"].split(" ")[0] if has_house_number else None
            point["street"] = " ".join(store["address1"].split(" ")[1:]) if has_house_number else store["address1"]
            point["city"] = store["city"]
            point["state"] = store["stateCode"]
            point["postcode"] = store["postalCode"]
            point["country"] = store["countryCode"]
            point["phone"] = store["phone"]
            point["website"] = website
            point["opening_hours"] = process_hours(store["storeHours"].replace("<br>", "; ").replace(" :", ": ").title())
            point["ref"] = store["number"]

            yield GeojsonPointItem(**point)
