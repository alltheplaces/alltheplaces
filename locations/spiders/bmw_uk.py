import scrapy

from locations.items import GeojsonPointItem
from locations.geo import point_locations


class BeerBmwUkSpider(scrapy.Spider):
    name = "bmw_uk"
    item_attributes = {
        "brand": "BMW",
        "brand_wikidata": "Q26678",
    }
    allowed_domains = ["bmw.co.uk"]

    def start_requests(self):
        point_files = "eu_centroids_120km_radius_country.csv"
        for lat, lon in point_locations(point_files):

            yield scrapy.Request(f"https://discover.bmw.co.uk/proxy/api/dealers?q={lat},{lon}&type=new")

    def parse(self, response):
        for data in response.json():
            properties = {
                "name": data.get("dealer_name").strip(),
                "city": data.get("town"),
                "ref": data.get("dealer_number"),
                "lon": data.get("longitude"),
                "lat": data.get("latitude"),
                "street_address": data.get("address_line_1").strip(),
                "phone": data.get("primary_phone"),
                "postcode": data.get("postcode"),
                "website": data.get("url"),
                "country": data.get("country"),
            }

            yield GeojsonPointItem(**properties)
