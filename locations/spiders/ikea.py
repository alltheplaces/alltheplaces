import json
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class IkeaSpider(scrapy.Spider):
    name = "ikea"
    item_attributes = {"brand": "IKEA", "brand_wikidata": "Q54078"}
    allowed_domains = ["ikea.com"]
    start_urls = [
        "https://www.ikea.com/ae/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/bh/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/eg/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/jo/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/kw/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ma/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/qa/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/sa/ar/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/cz/cs/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/dk/da/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/at/de/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/de/de/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/au/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ca/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/gb/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ie/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/in/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ph/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/sg/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/us/en/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/cl/es/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/es/es/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/mx/es/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/fi/fi/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/be/fr/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ch/fr/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/fr/fr/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/il/he/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/hr/hr/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/hu/hu/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/it/it/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/jp/ja/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/kr/ko/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/my/ms/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/nl/nl/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/no/no/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/pl/pl/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/pt/pt/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ro/ro/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ru/ru/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/sk/sk/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/si/sl/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/rs/sr/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/se/sv/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/th/th/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/ua/uk/meta-data/navigation/stores-detailed.json",
        "https://www.ikea.com/cn/zh/meta-data/navigation/stores-detailed.json",
    ]

    def parse(self, response):
        data = response.json()
        for store in data:
            if "storePageUrl" not in store:
                continue
            opening_hours = OpeningHours()
            for day in store["hours"]["normal"]:
                if day["open"] != "":
                    opening_hours.add_range(
                        day["day"][0:1].upper() + day["day"][1:2].lower(),
                        day["open"],
                        day["close"],
                    )
            properties = {
                "lat": store["lat"],
                "lon": store["lng"],
                "name": store["displayName"],
                "street_address": store["address"].get("street"),
                "city": store["address"].get("city"),
                "postcode": store["address"].get("zipCode"),
                "country": response.request.url[21:23].upper(),
                "website": store["storePageUrl"],
                "ref": store["id"],
                "opening_hours": opening_hours.as_opening_hours(),
                "extras": {
                    "store_type": store["buClassification"]["code"],
                },
            }

            if properties["country"] == "US":
                properties["state"] = store["address"].get("stateProvinceCode")[2:]

            yield GeojsonPointItem(**properties)
