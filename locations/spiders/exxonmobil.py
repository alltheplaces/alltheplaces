# -*- coding: utf-8 -*-
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
import json
from locations.items import GeojsonPointItem
import re


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
    base_url = (
        "https://www.exxon.com/en/api/locator/Locations?DataSource=RetailGasStations"
    )

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
        number_of_box = int(
            abs(row_width) / max_width + 1
        )  # safe to assume the are left overs
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
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

    def parse(self, response):
        json_data = json.loads(response.text)

        for location in json_data:
            location_id = location["LocationID"]
            if location_id not in self.crawled_locations:
                self.crawled_locations.add(location_id)
                features = location["FeaturedItems"] + location["StoreAmenities"]
                properties = {
                    "name": location["DisplayName"],
                    "addr_full": location["AddressLine1"]
                    + " "
                    + location["AddressLine2"],
                    "city": location["City"],
                    "state": location["StateProvince"],
                    "country": location["Country"],
                    "postcode": location["PostalCode"],
                    "phone": location["Telephone"],
                    "ref": location_id,
                    "opening_hours": self.store_hours(location["WeeklyOperatingDays"]),
                    "lat": float(location["Latitude"]),
                    "lon": float(location["Longitude"]),
                    "extras": {
                        "amenity:fuel": True,
                        "amenity:toilets": any(
                            "Restroom" in f["Name"] for f in features
                        ),
                        "atm": any("ATM" in f["Name"] for f in features),
                        "car_wash": any("Carwash" in f["Name"] for f in features),
                        "fuel:diesel": any("Diesel" in f["Name"] for f in features)
                        or None,
                        "fuel:octane_87": any("Regular" == f["Name"] for f in features)
                        or None,
                        "fuel:octane_89": any("Extra" == f["Name"] for f in features)
                        or None,
                        "fuel:octane_91": any("Supreme" == f["Name"] for f in features)
                        or None,
                        "fuel:octane_93": any("Supreme+" == f["Name"] for f in features)
                        or None,
                        "fuel:propane": any("Propane" == f["Name"] for f in features)
                        or None,
                        "shop": "convenience"
                        if any("Convenience Store" in f["Name"] for f in features)
                        else None,
                    },
                    **self.brand(location),
                }
                yield GeojsonPointItem(**properties)

    def brand(self, location):
        if "mobil" in location["BrandingImage"]:
            return {"brand": "Mobil", "brand_wikidata": "Q3088656"}
        elif "esso" in location["BrandingImage"]:
            return {"brand": "Esso", "brand_wikidata": "Q867662"}
        elif "exxon" in location["BrandingImage"]:
            return {"brand": "Exxon", "brand_wikidata": "Q109675651"}
        else:
            return {}

    def store_hours(self, hours):
        """
        convert hours, falls back to param hours if it fails our match

        :param hours: hours to convert come in format Monday:09:15 AM-09:15 PM<br>Tues...
        :return: our format 'Mo 04:30-23:00; Tu-Sa 04:30-23:30; Su 04:30-23:00'
        """
        hours_list = hours.split("<br/>")
        stripped_hours = [hour for hour in hours_list if hour]
        working_hours = []
        for hour in stripped_hours:
            match = re.search(
                r"^(\w{2})\w+:(?:(\d+):(\d+)\s(AM|PM)-(\d+):(\d+)\s(AM|PM))?(\w+)?(Open\s24\sHours)?$",
                hour.strip(),
            )
            if match:
                m = match.groups()
                if m[7] is None and m[8] is None:
                    # Open hours
                    working_hours.append(
                        m[0]
                        + " "
                        + str(int(m[1]) + self.am_pm(m[1], m[3])).zfill(2)
                        + ":"
                        + m[2]
                        + "-"
                        + str(int(m[4]) + self.am_pm(m[4], m[6])).zfill(2)
                        + ":"
                        + m[5]
                    )
                elif m[8] is not None:
                    working_hours.append(m[0] + ": 24/7")
                elif m[1] is None:
                    # closed
                    working_hours.append(m[0] + ": " + m[7])
        # we need to reduce the weekdays from something like
        # Mo 08:00-18:00, We 08:00-18:00, Th 08:00-18:00
        # to
        # Mo 08:00-18:00, We-Th 08:00-18:00
        # lets hold the previous working hour outside the loop
        prev_hours = ""
        final_working_hours = []
        # define how they should follow each other
        match_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for hour in working_hours:
            if hour[2:] != prev_hours[2:]:
                # hour being processed time range does not match previous
                # we let it be
                prev_hours = hour
                final_working_hours.append(hour)
            else:
                # hour matches, let's try to compress
                last_entry = final_working_hours[-1]
                # get index of what the day of prev_hour should be if we have to compress this
                get_prev_index = match_order.index(hour[0:2]) - 1
                if last_entry[-14:-12] == match_order[get_prev_index]:
                    # day of previous append complies with out match_order
                    p = final_working_hours.pop(-1)
                    final_working_hours.append(
                        p[0:2] + "-" + hour[0:2] + prev_hours[-12:]
                    )
                    prev_hours = hour
                elif (
                    last_entry[-8:-6] == match_order[get_prev_index]
                    and hour[-4:] == "24/7"
                ):
                    # lets do same for 24/7, they have this wierd Mon 24/7, Tue 24/7 etc
                    p = final_working_hours.pop(-1)
                    final_working_hours.append(
                        p[0:2] + "-" + hour[0:2] + prev_hours[-6:]
                    )
                    prev_hours = hour
                else:
                    # no match, let it be
                    final_working_hours.append(hour)

        if final_working_hours:
            return "; ".join(final_working_hours)
        elif hours == "Open 24 Hours":
            # there is also a scenario where, 24/7 has no day of week prepended.
            return "24/7"
        else:
            # if it all fails
            return hours

    def am_pm(self, hr, a_p):
        """
            A convenience method to fix noon and midnight issues
        :param hr: the hour has to be passed in to accurately decide 12noon and midnight
        :param a_p: this is either a or p i.e am pm
        :return: the hours that must be added
        """
        diff = 0
        if a_p == "AM":
            if int(hr) < 12:
                diff = 0
            else:
                diff = -12
        else:
            if int(hr) < 12:
                diff = 12
        return diff
