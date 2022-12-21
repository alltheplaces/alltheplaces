import csv
import json

import scrapy

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su",
}

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://spatial.virtualearth.net/REST/v1/data/ab055fcbaac04ec4bc563e65ffa07097/Filialdaten-SEC/Filialdaten-SEC?$select=*,__Distance&$filter=Adresstyp%20eq%201&key=AiUPPcYK4rdGkNaJ9FLpcgcgcEfzdPNcqEafbU8B6m8hzjcQk_urZxCWtLvFsHSq&$format=json&jsonp=Microsoft_Maps_Network_QueryAPI_3&spatialFilter=nearby({:},{:},40.1931215)"


class LidlDESpider(scrapy.Spider):
    name = "lidl_de"
    item_attributes = {
        "brand": "Lidl",
        "brand_wikidata": "Q151954",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    handle_httpstatus_list = [404]

    def start_requests(self):
        with open("locations/searchable_points/germany_grid_15km.csv") as openFile:
            results = csv.DictReader(openFile)
            for result in results:
                longitude = float(result["longitude"])
                latitude = float(result["latitude"])
                request = scrapy.Request(
                    url=STORELOCATOR.format(latitude, longitude),
                    headers=HEADERS,
                    callback=self.parse,
                )
                yield request

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hoursAll = hours.split("<br>")
        for item in hoursAll:
            if item.split():
                try:
                    day = DAY_MAPPING[item.split()[0]]
                    hour = item.split()[1]
                    opening_hours.add_range(
                        day=day,
                        open_time=hour.split("-")[0],
                        close_time=hour.split("-")[1],
                    )
                except KeyError:
                    pass

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.body.decode("utf-8").split("Microsoft_Maps_Network_QueryAPI_3(")[1]
        fixed_data = data.rstrip(data[-1])
        jsonData = json.loads(fixed_data)
        shops_of_the_area = jsonData["d"]["results"]

        shop_property = {}

        for shop in shops_of_the_area:
            shop_property["ref"] = shop["EntityID"]
            shop_property["country"] = shop["CountryRegion"]
            shop_property["city"] = shop["Locality"]
            shop_property["postcode"] = shop["PostalCode"]
            shop_property["street"] = shop["AddressLine"]
            shop_property["lat"] = shop["Latitude"]
            shop_property["lon"] = shop["Longitude"]
            hours = self.parse_hours(shop["OpeningTimes"])
            if hours:
                shop_property["opening_hours"] = hours

            yield GeojsonPointItem(**shop_property)
