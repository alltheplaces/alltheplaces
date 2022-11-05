import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class OliveGardenSpider(scrapy.Spider):
    name = "olivegarden"
    item_attributes = {"brand": "Olive Garden", "brand_wikidata": "Q3045312"}
    allowed_domains = ["olivegarden.com"]
    start_urls = [
        "https://www.olivegarden.com/en-locations-sitemap.xml",
    ]

    def parse(self, response):
        response.selector.remove_namespaces()
        for loc in response.xpath("//loc/text()").extract():
            ref = int(loc.split("/")[-1])
            url = f"https://www.olivegarden.com/web-api/restaurant/{ref}?locale=en_US&restNumFlag=true&restaurantNumber={ref}"
            yield scrapy.Request(url, self.parse_restaurant, meta={"website": loc})

    def parse_restaurant(self, response):
        data = response.json()["successResponse"]["restaurantDetails"]
        # Field is named longitudeLatitude and contains latitude, longitude.
        lat, lon = data["address"]["longitudeLatitude"].split(",")
        properties = {
            "lon": lon,
            "lat": lat,
            "website": response.meta["website"],
            "ref": data["restaurantNum"],
            "name": data["restaurantName"],
            "street_address": data["address"]["address1"],
            "city": data["address"]["city"],
            "state": data["address"]["state"],
            "postcode": data["address"]["zipCode"],
            "country": data["address"]["country"],
            "phone": data["restPhoneNumber"][0]["Phone"],
            "opening_hours": self.parse_hours(data),
        }
        yield GeojsonPointItem(**properties)

    @staticmethod
    def parse_hours(data):
        oh = OpeningHours()
        # Sun = 1, Sat = 7
        day = lambda d: data["daysOfWeeks"][d - 1][:2].title()
        for row in data["weeklyHours"]:
            if row["hourTypeDesc"] == "Hours of Operations":
                oh.add_range(
                    day(row["dayOfWeek"]), row["startTime"], row["endTime"], "%I:%M%p"
                )
        return oh.as_opening_hours()
