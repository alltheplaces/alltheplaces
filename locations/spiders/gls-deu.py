import scrapy
import json
import csv
from locations.items import GeojsonPointItem

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://api.gls-pakete.de/parcelshops?version=4&coordinates={},{}&distance=40"

class GenspiderSpider(scrapy.Spider):
    name = 'glsdeuSpider'
    allowed_domains = ['https://www.gls-pakete.de/']
    deList = []
    usedLongLat = []

    def start_requests(self):
        searchable_point_files = [
            "./locations/searchable_points/eu_centroids_40km_radius_country.csv",
        ]

        for point_file in searchable_point_files:
            with open(point_file) as openFile:
                results = csv.DictReader(openFile)
                for result in results:
                    if(result["country"] == "DE"):
                        longitude = format(float(result["longitude"]), '.5f')
                        latitude = format(float(result["latitude"]), '.5f')
                        request = scrapy.Request(
                            url=STORELOCATOR.format(str(latitude), str(longitude)),
                            headers=HEADERS,
                            callback=self.parse,
                        )
                        yield request

    def parse(self, response):
        firstResults = json.loads(response.body)
        results = firstResults['shops']
        item = GeojsonPointItem()

        for result in results:
            address = result['address']
            phone = result['phone']
            coordinates = address['coordinates']
            longitude = coordinates['longitude']
            latitude = coordinates['latitude']
            name = address['name']
            openingHours = result['openingHours']
            state = 1

            item['name'] = name
            item["lat"] = latitude
            item["lon"] = longitude
            item["street"] = address["street"]
            item["housenumber"] = address['houseNumber']
            item["city"] = address['city']
            item["postcode"] = address['postalCode']
            item["phone"] = phone['number']
            item["opening_hours"] = openingHours

            if(GenspiderSpider.usedLongLat):
                for used in GenspiderSpider.usedLongLat:
                    if (used["longitude"] == longitude and used["latitude"] == latitude):
                        state = 0

            if(state == 1):
                data = {
                    "longitude": longitude,
                    "latitude": latitude
                }
                GenspiderSpider.usedLongLat.append(data)
                yield item