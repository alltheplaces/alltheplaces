from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class JeffDeBrugesSpider(Spider):
    name = "jeff_de_bruges"
    item_attributes = {
        "brand": "Jeff de Bruges",
        "brand_wikidata": "Q3176626",
        "extras": Categories.SHOP_CHOCOLATE.value,
    }
    allowed_domains = ["www.jeff-de-bruges.com"]
    start_urls = ["https://www.jeff-de-bruges.com/ajax.V1.php/fr_FR/Rbs/Storelocator/Store/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        data = {
            "websiteId": 100198,
            "sectionId": 100198,
            "pageId": 101426,
            "data": {
                "currentStoreId": 0,
                "distanceUnit": "kilometers",
                "distance": "50000kilometers",
                "coordinates": {"latitude": 0, "longitude": 0},
                "commercialSign": 0,
            },
            "dataSets": "coordinates,address,card,allow,hours",
            "URLFormats": "canonical,contextual",
            "visualFormats": "original,95x95,190x190,290x188,384x249,580x376,768x498,1160x752,1536x996",
            "pagination": "0,5000",
            "referer": "https://www.jeff-de-bruges.com/trouver-une-boutique",
        }
        yield JsonRequest(url=self.start_urls[0], data=data, headers={"X-HTTP-Method-Override": "GET"}, method="POST")

    def parse(self, response):
        for location in response.json()["items"]:
            properties = {
                "ref": location["common"].get("code"),
                "name": location["common"].get("title"),
                "lat": location["coordinates"].get("latitude"),
                "lon": location["coordinates"].get("longitude"),
                "street_address": location["address"]["fields"].get("street"),
                "city": location["address"]["fields"].get("locality"),
                "postcode": location["address"]["fields"].get("zipCode"),
                "country": location["address"]["fields"].get("countryCode"),
                "website": location["common"]["URL"].get("canonical"),
                "opening_hours": OpeningHours(),
            }

            if location.get("card"):
                properties["phone"] = location["card"].get("phone")
                properties["email"] = location["card"].get("email")

            if location["common"].get("visuals"):
                properties["image"] = location["common"]["visuals"][0].get("original")

            for day_hours in location["hours"].get("openingHours"):
                day_name = day_hours["title"]
                morning_start = day_hours["amBegin"]
                morning_end = day_hours["amEnd"]
                afternoon_start = day_hours["pmBegin"]
                afternoon_end = day_hours["pmEnd"]
                if morning_start and not morning_end and not afternoon_start and afternoon_end:
                    properties["opening_hours"].add_range(DAYS_FR[day_name], morning_start, afternoon_end)
                elif morning_start and morning_end and afternoon_start and afternoon_end:
                    properties["opening_hours"].add_range(DAYS_FR[day_name], morning_start, morning_end)
                    properties["opening_hours"].add_range(DAYS_FR[day_name], afternoon_start, afternoon_end)

            yield Feature(**properties)
