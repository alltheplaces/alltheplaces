"""
Exxonmobil has 1,679 locations worldwide except a few nations(those may even change with time)
This crawler crawls https://www.exxon.com/en/api/locator/Locations
with 4 parameters representing a bounding box of latitudes and longitudes.

We created an extra class CreateStartURLs to keep things neat,
this class has a boxes attribute which is a dict of tuples(lat1, lon1, lat2, lon2, max_width, max_height)
      boxes = {
            "upper_canada": (71.57, -169.73, 58.43, -60.57, 3, 3),  # maxresult=6
            "lower_canada": (58.89, -139.32, 45.44, -51.96,2,2),  # maxresult=98
            "upper_usa": (48.67, -129.3, 42.92, -57.94, 0.7,0.7),  # maxresult=130
            "middle_usa": (44.4, -126.3, 34.86, -68.30, 0.6, 0.6),  # maxresult=163
            ...
Countries without Exxonmobil's presence e.g Russia, iceland etc have their box sizes
enlarged via max_width and max_height which occupy the last 2 indices per large box
 for efficiency sake.

Each tuple represents a large box, we then loop through from left to right/up to down
with a mini box size to cover the large box.
It looked like they have 15,000+ locations until i introduced the python's set()
using the returned LocationID as unique keys for each location.
I just pray LocationID is actually unique

max_width and max_height have been optimized to return less than 250 results, which is the max
result returned from exxonmobil no matter how big the boundingbox is.

"""

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.costacoffee_gb import yes_or_no
from locations.user_agents import BROWSER_DEFAULT


class CreateStartURLs:
    # comment out large boxes to further improve crawl time when needed
    boxes = {
        "upper_canada": (71.57, -169.73, 58.43, -60.57, 3, 3),  # maxresult=6
        "lower_canada": (58.89, -139.32, 45.44, -51.96, 2, 2),  # maxresult=98
        "upper_usa": (48.67, -129.3, 42.92, -57.94, 0.7, 0.7),  # maxresult=130
        "middle_usa": (44.4, -126.3, 34.86, -68.30, 0.6, 0.6),  # maxresult=163
        "southern_usa": (36.292, -122.975, 25.93, -73.41, 0.6, 0.6),  # maxresult=186
        "caribbean_sea": (25.77, -115.59, 14.917, -62.506, 2, 2),  # maxresult =69
        "caribbean_sea_2": (14.74, -95.37, 11.32, -77.45, 2, 2),  # maxresult=0
        "middlebelt_america": (10.28, -87.11, 0, -47.39, 2, 2),  # maxresult=0
        "middlebelt_america_2": (0, -83.42, -19.17, -33.68, 2, 2),  # maxresult=0
        "middle_south_america": (-15.98, -74.46, -29.40, -37.195, 3, 3),  # maxresult=0
        "south_america": (-28.32, -77.10, -42.90, -50.36, 3, 3),  # maxresult=0
        "south_america_2": (-41.60, -77.07, -55.65, -60.03, 3, 3),  # maxresult=0
        "europe": (59.29, -14.68, 36.49, 52.65, 1, 1),  # maxresult=197
        "west_africa": (36.0, -19.07, 3.91, 57.74, 3, 3),  # maxresult=64
        "south_africa": (3.56, 7.64, -33.97, 40.52, 3, 3),  # maxresult=0
        "india_china": (45.85, 48.96, 21.17, 123.66, 3, 3),  # maxresult=47
        "india": (24.57, 66.35, 5.32, 87.45, 3, 3),  # max-result=0
        "vietnam": (22.32, 90.97, 8.46, 111.53, 1, 1),  # max-result=215
        "indonesia": (9.154, 93.42, -11.47, 155, 2, 2),  # maxresult=55
        "australia": (-10.78, 112.24, -38.92, 154.77, 3, 3),  # maxresult=13
        "australia_2": (-40.27, 142.99, -44.18, 149.15, 3, 3),  # maxresult=0
        "lower_newzealand": (-40.13, 166, -46.52, 176.22, 3, 3),  # maxresult=45
        "upper_newzealand": (-33.24, 171.29, -41.73, 178.86, 3, 3),  # maxresult=149
        "russia": (70.49, 2.52, 46.06, 146.3, 5, 5),  # maxresult=0
        "iceland": (67.4, -25.43, 63.3, -13.13, 2, 2),  # maxresult=0
        "magadascar": (-11.29, 42.80, -26.07, 50.89, 1, 1),  # maxresult=0
    }
    urls = []
    base_url = "https://www.exxon.com/en/api/locator/Locations?DataSource=RetailGasStations"

    def __init__(self):
        self.build_start_urls()

    def build_start_urls(self):
        """
        Build the URLs with the max width and max height
        each largebox has it's own width and height
        That way, we dont spend much time on some large boxes
        only to figure they have 0 locations
        :return:
        """
        for box_name, box in self.boxes.items():
            # for readability sake
            lat1 = box[0]
            lon1 = box[1]
            lat2 = box[2]
            lon2 = box[3]
            max_w = box[4]
            max_h = box[5]
            for row in self.get_vertical(lat1, lat2, max_h):
                for col in self.get_horizontal(row, lon1, lon1 - lon2, max_w, max_h):
                    self.urls.append(
                        self.base_url
                        + "&Latitude1="
                        + str(min(col[0], col[2]))
                        + "&Longitude1="
                        + str(min(col[1], col[3]))
                        + "&Latitude2="
                        + str(max(col[0], col[2]))
                        + "&Longitude2="
                        + str(max(col[1], col[3]))
                    )

    def get_urls(self):
        """
        URL getter
        :return: tuple of URLs built by build_start_urls
        """
        return tuple(self.urls)

    def get_horizontal(self, start_lat, start_lon, row_width, max_width, max_height):
        """
        Left to right box movement
        :param start_lat: starting latitude
        :param start_lon: starting longitude
        :param row_width: Width of the large box
        :param max_width: maximum width for this
        :param max_height: maximum height
        :return:
        """
        number_of_box = int(abs(row_width) / max_width + 1)  # safe to assume the are left overs
        for box in range(abs(number_of_box)):
            b_lon_left = start_lon
            b_lat_left = start_lat
            b_lon_right = b_lon_left + max_width
            b_lat_right = b_lat_left - max_height
            start_lon = b_lon_right
            start_lat = b_lat_right + max_height
            yield (b_lat_left, b_lon_left, b_lat_right, b_lon_right)

    def get_vertical(self, start_point, end_point, max_height):
        """
        Logic that helps us jump to the next line from up to down
        we need latitudes because we are jumping down on same longitude
        :param start_point: starting latitude
        :param end_point: ending latitude
        :param max_height: max height to move by
        :return:
        """
        difference = start_point - end_point
        number_of_boxes = int(difference / max_height + 1)
        # the first box must be included
        start_point += max_height
        for box in range(number_of_boxes):
            b_lat = start_point - max_height
            start_point = b_lat
            yield b_lat


class ExxonMobilSpider(scrapy.Spider):
    name = "exxonmobil"
    item_attributes = {"brand": "ExxonMobil", "brand_wikidata": "Q156238"}
    crawled_locations = set()
    allowed_domains = ["exxon.com"]
    start_urls = CreateStartURLs().get_urls()
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        json_data = response.json()

        for location in json_data:
            location_id = location["LocationID"]
            if location_id not in self.crawled_locations:
                self.crawled_locations.add(location_id)
                features = location["FeaturedItems"] + location["StoreAmenities"]
                properties = {
                    "name": location["DisplayName"],
                    "street_address": ", ".join(filter(None, [location["AddressLine1"], location["AddressLine2"]])),
                    "city": location["City"],
                    "state": location["StateProvince"],
                    "country": location["Country"],
                    "postcode": location["PostalCode"],
                    "phone": location["Telephone"],
                    "ref": location_id,
                    "opening_hours": self.store_hours(location["HoursOfOperation24"]),
                    "lat": float(location["Latitude"]),
                    "lon": float(location["Longitude"]),
                    "extras": {
                        "amenity": "fuel",
                        "toilets": yes_or_no(any("Restroom" in f["Name"] for f in features)),
                        "atm": yes_or_no(any("ATM" in f["Name"] for f in features)),
                        "car_wash": yes_or_no(any("Carwash" in f["Name"] for f in features)),
                        "fuel:diesel": yes_or_no(any("Diesel" in f["Name"] for f in features)),
                        "fuel:octane_87": yes_or_no(any("Regular" == f["Name"] for f in features)),
                        "fuel:octane_89": yes_or_no(any("Extra" == f["Name"] for f in features)),
                        "fuel:octane_91": yes_or_no(any("Supreme" == f["Name"] for f in features)),
                        "fuel:octane_93": yes_or_no(any("Supreme+" == f["Name"] for f in features)),
                        "fuel:propane": yes_or_no(any("Propane" == f["Name"] for f in features)),
                        "shop": "convenience" if any("Convenience Store" in f["Name"] for f in features) else "no",
                    },
                    **self.brand(location),
                }
                yield Feature(**properties)

    def brand(self, location):
        if "mobil" in location["BrandingImage"]:
            return {"brand": "Mobil", "brand_wikidata": "Q3088656"}
        elif "esso" in location["BrandingImage"]:
            return {"brand": "Esso", "brand_wikidata": "Q867662"}
        elif "exxon" in location["BrandingImage"]:
            return {"brand": "Exxon", "brand_wikidata": "Q109675651"}
        else:
            return {"brand": location["BrandingImage"]}

    @staticmethod
    def store_hours(hours: str) -> OpeningHours:
        """
        :param hours: hours to convert come in format "04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;04:00,23:00;"
        :return: OpeningHours
        """
        oh = OpeningHours()
        for index, times in enumerate(hours.strip(";").split(";")):
            if not times or times == "Closed":
                continue
            if times == "All Day":
                times = "00:00,23:59"
            try:
                start_time, end_time = times.split(",")
                oh.add_range(DAYS[index], start_time, end_time)
            except:  # A few edge cases like "2200" not "22:00"
                pass

        return oh
