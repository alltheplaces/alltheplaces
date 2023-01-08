import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class BunningsSpider(scrapy.Spider):
    name = "bunnings"
    allowed_domains = ["bunnings.com.au"]
    start_urls = ("https://api.prod.bunnings.com.au/v1/stores/country/AU?fields=FULL",)
    item_attributes = {"brand": "Bunnings", "brand_wikidata": "Q4997829"}
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IkJGRTFEMDBBRUZERkVDNzM4N0E1RUFFMzkxNjRFM0MwMUJBNzVDODciLCJ4NXQiOiJ2LUhRQ3VfZjdIT0hwZXJqa1dUandCdW5YSWMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2J1bm5pbmdzLmNvbS5hdS8iLCJuYmYiOjE2NzE5Nzc2NTksImlhdCI6MTY3MTk3NzY1OSwiZXhwIjoxNjcyNDA5NjU5LCJhdWQiOlsiQ2hlY2tvdXQtQXBpIiwiY3VzdG9tZXJfYnVubmluZ3MiLCJodHRwczovL2J1bm5pbmdzLmNvbS5hdS9yZXNvdXJjZXMiXSwic2NvcGUiOlsiY2hrOmV4ZWMiLCJjbTphY2Nlc3MiLCJlY29tOmFjY2VzcyIsImNoazpwdWIiXSwiYW1yIjpbImV4dGVybmFsIl0sImNsaWVudF9pZCI6ImJ1ZHBfZ3Vlc3RfdXNlcl9hdSIsInN1YiI6IjA3YWNlYzQ5LTcwNDEtNDZhZS05NTUwLTU3MTMxMDJiZTMyZSIsImF1dGhfdGltZSI6MTY3MTk3NzY1OCwiaWRwIjoibG9jYWxsb29wYmFjayIsImItaWQiOiIwN2FjZWM0OS03MDQxLTQ2YWUtOTU1MC01NzEzMTAyYmUzMmUiLCJiLXJvbGUiOiJndWVzdCIsImItdHlwZSI6Imd1ZXN0IiwibG9jYWxlIjoiZW5fQVUiLCJiLWNvdW50cnkiOiJBVSIsInVzZXJfbmFtZSI6IjA3YWNlYzQ5LTcwNDEtNDZhZS05NTUwLTU3MTMxMDJiZTMyZSIsImFjdGl2YXRpb25fc3RhdHVzIjoiRmFsc2UiLCJiLXJiYWMiOlt7ImFzYyI6Ijc4NTUyZDhlLTIyMDItNDA4Zi04OGJlLWFiMzlhODZlY2QwZCIsInR5cGUiOiJDIiwicm9sIjpbIkNISzpHdWVzdCIsIkNISzpHdWVzdCJdfV0sInNpZCI6IjhGRDIwMDk4NTZFNDE1RTIwNUI4M0JFQzU4QzgwMTg0IiwianRpIjoiM0YxMzUxQ0E2NzdGREVCNzY4RUZDOTREMDVEMzYwMjEifQ.qAaoeuVbKECBttFWEdv4rguiiNWgW0091bw9klcdESBW6llp8YmYq0-TDEbNN0gilb385czPcbRWNMl0Uigh3hNjlNPc5InEcSEsRiKFXE1bm_R2X5WzEI47OmtRAogC5zuQThk-u_WRuc3C3pHw2Bu2x3kZ6QQpo9RjjNtyGL_CnC6GL_VzK_T1wZHKDMmVctozLmkIhf3KLas7x0AzpRHfKeZO68cR62oxwW0RTMK01EwdHy9_7X9vnb0Duvb-R1h0VLjGhqU6fWgmgMNuNsvW2Rlsh4ZQz0uGIwT_LNZbYRA4tcacdt-Oie_egmF6KjLdg-VXTkUmV35Nc7HPtg",
            "clientId": "mHPVWnzuBkrW7rmt56XGwKkb5Gp9BJMk",
            "country": "AU",
            "locale": "en_AU",
        }
    }

    def parse(self, response):
        data = response.json().get("data", {}).get("pointOfServices")
        for store in data:
            oh = OpeningHours()
            for day in store.get("openingHours", {}).get("weekDayOpeningList"):
                oh.add_range(
                    day=day.get("weekDay"),
                    open_time=day.get("openingTime", {}).get("formattedHour"),
                    close_time=day.get("closingTime", {}).get("formattedHour"),
                    time_format="%I:%M %p",
                )

            properties = {
                "ref": store.get("address", {}).get("id"),
                "name": store.get("displayName"),
                "lat": store.get("geoPoint", {}).get("latitude"),
                "lon": store.get("geoPoint", {}).get("longitude"),
                "street_address": store.get("address", {}).get("formattedAddress"),
                "city": store.get("pricingRegion"),
                "postcode": store.get("address", {}).get("postalCode"),
                "country": store.get("country", {}).get("isocode"),
                "phone": store.get("address", {}).get("phone"),
                "email": store.get("address", {}).get("email"),
                "website": f'https://www.bunnings.com.au/stores/{store.get("storeRegion").lower()}/{store.get("displayName").lower().replace(" ", "-")}',
                "opening_hours": oh.as_opening_hours(),
            }

            yield Feature(**properties)
