import scrapy

from locations.geo import point_locations
from locations.items import GeojsonPointItem


class DaciaFrSpider(scrapy.Spider):
    name = "dacia_fr"
    item_attributes = {
        "brand": "Dacia",
        "brand_wikidata": "Q27460",
    }
    allowed_domains = ["dacia.fr"]

    def start_requests(self):
        point_files = "eu_centroids_20km_radius_country.csv"
        for lat, lon in point_locations(point_files, "FR"):
            yield scrapy.Request(
                f"https://www.dacia.fr/wired/commerce/v1/dealers/locator?lat={lat}&lon={lon}&language=fr&country=fr&filters=dacia.blacklisted%3D%3Dfalse&count=10000000&renaultChoice=true",
            )

    def parse(self, response):
        for data in response.json():
            if not data.get("blacklisted"):
                item = GeojsonPointItem()
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
