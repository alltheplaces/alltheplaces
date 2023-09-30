import scrapy
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


class DrMaxSpider(scrapy.Spider):
    name = "dr_max"
    item_attributes = {"brand": "Dr. Max", "brand_wikidata": "Q56317371"}

    start_urls = [
        "https://pharmacy.drmax.pl/api/v1/public/pharmacies",
        "https://pharmacy.drmax.cz/api/v1/public/pharmacies",
        "https://pharmacy.drmax.sk/api/v1/public/pharmacies",
        "https://pharmacy.drmax.it/api/v1/public/pharmacies",
    ]

    website_roots = [
        "https://www.drmax.pl/apteki/",
        "https://www.drmax.cz/lekarny/",
        "https://www.drmax.sk/lekarne/",
        "https://www.drmax.it/le-nostre-farmacie/",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]:
            tld = response.url.split("/")[2].split(".")[-1]

            # copy location.location to the root of the object
            location.update(location.pop("location"))
            item = DictParser.parse(location)
            item.pop("street")
            item["street_address"] = location["street"]
            item["name"] = location["pharmacyPublicName"]
            if len(location["phoneNumbers"]) > 0:
                item["phone"] = location["phoneNumbers"][0]["number"]
            item["email"] = location.get("additionalParams").get("email")
            item["image"] = location["pharmacyImage"]
            item["country"] = tld
            service_ids = [service["serviceId"] for service in location["services"]]
            apply_yes_no(Extras.WHEELCHAIR, item, "WHEELCHAIR_ACCESS" in service_ids)
            root_url = self.website_roots[self.start_urls.index(response.url)]
            item["website"] = root_url + location["urlKey"]
            yield item
