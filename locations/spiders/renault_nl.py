import scrapy

from locations.geo import point_locations
from locations.items import Feature


class RenaultNLSpider(scrapy.Spider):
    name = "renault_nl"
    item_attributes = {
        "brand": "Renault",
        "brand_wikidata": "Q6686",
    }

    def start_requests(self):
        point_files = "eu_centroids_80km_radius_country.csv"
        for lat, lon in point_locations(point_files, "NL"):
            yield scrapy.Request(
                f"https://www.renault.nl/wired/commerce/v1/dealers/locator?lat={lat}&lon={lon}&country=nl&language=nl&filters=renault.blacklisted%3D%3Dfalse%3Brenault.receiveLead%3D%3Dtrue&count=25000",
            )

    def parse(self, response):
        for data in response.json():
            if not data.get("blacklisted"):
                item = Feature()
                item["ref"] = data.get("dealerId")
                item["name"] = data.get("name")
                item["country"] = data.get("country")
                item["lat"] = data.get("geolocalization", {}).get("lat")
                item["lon"] = data.get("geolocalization", {}).get("lon")
                item["city"] = data.get("regionalDirectorate")
                item["postcode"] = data.get("address", {}).get("postalCode")
                item["street_address"] = data.get("address", {}).get("streetAddress")
                item["phone"] = data.get("telephone", {}).get("value")

                yield item
