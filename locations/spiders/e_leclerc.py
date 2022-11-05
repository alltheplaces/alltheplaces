import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class ELeclercSpider(scrapy.Spider):
    name = "e_leclerc"
    item_attributes = {"brand": "E.Leclerc", "brand_wikidata": "Q1273376"}
    allowed_domains = ["e-leclerc.com", "api.woosmap.com"]

    key = "woos-6256d36f-af9b-3b64-a84f-22b2342121ba"
    headers = {
        "origin": "https://www.e.leclerc",
    }

    day_range = {
        1: "Mo",
        2: "Tu",
        3: "We",
        4: "Th",
        5: "Fr",
        6: "Sa",
        7: "Su",
    }

    def start_requests(self):
        yield scrapy.Request(
            url=f"https://api.woosmap.com/stores/search?key={self.key}&lat=48.860245&lng=2.378051&stores_by_page=300&limit=300&page=1",
            method="GET",
            callback=self.parse,
            headers=self.headers,
        )

    def parse(self, response):
        json_obj = response.json()
        pagination = json_obj.get("pagination")
        for store in json_obj["features"]:
            store_properties = store.get("properties")
            contact = store_properties.get("contact")
            address = store_properties.get("address")
            user_properties = store_properties.get("user_properties")
            coords = store.get("geometry").get("coordinates")
            email = contact.get("email")
            opening_hours = OpeningHours()
            usual_oh = store_properties.get("opening_hours").get("usual")
            for day_count in usual_oh if usual_oh else []:
                if len(usual_oh.get(day_count)) >= 1:
                    dates = usual_oh.get(day_count)[0]
                    if dates["start"] != "":
                        opening_hours.add_range(
                            self.day_range.get(int(day_count)),
                            dates["start"],
                            dates["end"],
                        )

            properties = {
                "name": f"E.Leclerc {store_properties.get('name')}",
                "ref": store_properties.get("store_id"),
                "street_address": address.get("lines")[0],
                "city": address.get("city"),
                "postcode": address.get("zipcode"),
                "country": address.get("country_code"),
                "phone": contact.get("phone"),
                "website": user_properties.get("urlStore"),
                "opening_hours": opening_hours.as_opening_hours(),
                "lat": coords[1],
                "lon": coords[0],
                "email": email,
                "extras": {
                    "store_type": user_properties.get("commercialActivity").get("label")
                    if user_properties.get("commercialActivity")
                    else ""
                },
            }

            yield GeojsonPointItem(**properties)

        if pagination.get("page") != pagination.get("pageCount"):
            next_page = pagination.get("page") + 1
            yield scrapy.Request(
                f"https://api.woosmap.com/stores/search?key={self.key}&lat=48.860245&lng=2.378051&stores_by_page=300&limit=300&page={next_page}",
                callback=self.parse,
                headers=self.headers,
            )
