import scrapy

from locations.geo import point_locations
from locations.items import Feature


class BeerMappingSpider(scrapy.Spider):
    name = "beermapping"
    allowed_domains = ["beermapping.com"]
    download_delay = 3

    def start_requests(self):
        point_files = "us_centroids_100mile_radius.csv"
        for lat, lon in point_locations(point_files):
            yield scrapy.Request(
                f"https://www.{self.allowed_domains[0]}/includes/dataradius.php?lat={lat}&lng={lon}&radius=500"
            )

    def parse(self, response):
        try:
            results = response.json()
        except ValueError:
            return
        if not results["count"]:
            return
        results = results["locations"]
        for data in results:
            properties = {
                "name": data["name"],
                "city": data["city"],
                "ref": data["id"],
                "lon": data["lng"],
                "lat": data["lat"],
                "addr_full": data["street"],
                "phone": data["phone"],
                "state": data["state"],
                "postcode": data["zip"],
                "website": data["url"],
            }

            yield Feature(**properties)
