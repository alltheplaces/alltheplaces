import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points


class HopdoddyBurgerBarSpider(scrapy.Spider):
    name = "hopdoddy_burger_bar"
    allowed_domains = ["amazonaws.com"]

    def start_requests(self):
        base_url = "https://na6c0i4fb0.execute-api.us-west-2.amazonaws.com/restaurants/near?lat={lat}3&long={lon}"

        with open_searchable_points("us_centroids_25mile_radius.csv") as points:
            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(",")

                url = base_url.format(lat=lat, lon=lon)

                yield scrapy.http.Request(url, callback=self.parse)

    def parse(self, response):
        data = response.json()

        for place in data["restaurants"]:
            properties = {
                "ref": place["id"],
                "name": place["name"],
                "street_address": place["streetaddress"],
                "city": place["city"],
                "state": place["state"],
                "postcode": place["zip"],
                "country": place["country"],
                "lat": place["latitude"],
                "lon": place["longitude"],
                "phone": place["telephone"],
            }

            yield Feature(**properties)
