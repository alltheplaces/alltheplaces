# -*- coding: utf-8 -*-
"""

"""
import scrapy
import json
from locations.items import GeojsonPointItem
import re

def logme(text, f):
    h=open(f, "a")
    h.write(str(text)+"\n")
    h.close()

max_width=0.75
max_height=0.75

def get_horizontal(start_lat, start_lon, row_width):
    number_of_box = int(abs(row_width) / max_width + 1)  # safe to assume the are left overs
    for box in range(abs(number_of_box)):
        b_lon_left = start_lon
        b_lat_left = start_lat
        b_lon_right = b_lon_left + max_width
        b_lat_right = b_lat_left - max_height
        start_lon = b_lon_right
        start_lat = b_lat_right + max_height
        yield (b_lat_left, b_lon_left, b_lat_right, b_lon_right)

def get_vertical(start_point, end_point):
    difference = start_point - end_point
    number_of_boxes = int(difference / max_height + 1)
    # the first box must be included
    start_point += max_height
    for box in range(number_of_boxes):
        b_lat = start_point - max_height
        start_point = b_lat
        yield b_lat

boxes = [
    #(71.57, -169.73, 58.43, -60.57), #upper canada
    #(58.89, -139.32, 45.44, -51.96), #lower canada
    (48.67,-129.3, 42.92, -57.94), #upper USA
    (44.4, -126.3, 34.86, -68.30), #middle USA
    # (36.292, -122.975, 25.93,-73.41), #southern USA
    # (25.77, -115.59, 14.917, -62.506), #Caribbean sea
    # (14.74, -95.37, 11.32, -77.45), #Caribbean sea 2
    # (10.28, -87.11, 0, -47.39),     #Middlebelt America
    # (0, -83.42, -19.17, -33.68),    #Middlebelt America 2
    # (-15.98, -74.46, -29.40, -37.195), # Middle South America
    # (-28.32, -77.10, -42.90, -50.36),
    # (-41.60, -77.07, -55.65, -60.03), # UK
    # (59.29, -14.68, 36.49, 52.65),  #Europe
    # (36.0, -19.07, 3.91, 57.74),    #West Africa
    # (3.56, 7.64, -33.97, 40.52),    # South Africa
    # (45.85, 48.96, 21.17, 123.66),  # India/China
    # (24.57, 66.35, 5.32, 87.45),    # India X
    # (22.32, 90.97, 8.46, 111.53),   # Vietnam
    # (9.154, 93.42, -11.47, 155),    # Indeonesia
    # (-10.78, 112.24, -38.92, 154.77), # Australia
    # (-40.27, 142.99, -44.18, 149.15), # Australia X
    # (-40.13, 166, -46.52, 176.22),  # Lower Newzealand
    # (-33.24, 171.29, -41.73, 178.86), # Upper Newzealand
    # (70.49, 2.52, 46.06, 146.3),    # Russia  X
    # (67.4, -25.43, 63.3, -13.13)    # Iceland X
]

base_url = 'http://www.exxon.com/api/v1/Retail/retailstation/GetStationsByBoundingBox?'
urls=[]
for box in boxes:
    #for readability sake
    lat1=box[0]
    lon1=box[1]
    lat2=box[2]
    lon2=box[3]
    for row in get_vertical(lat1, lat2):
        for col in get_horizontal(row, lon1, lon1 - lon2):
            urls.append(base_url + "Latitude1="+str(col[0])+"&Longitude1="+str(col[1])+"&Latitude2="+str(col[2])+"&Longitude2="+str(col[3]))

class ExxonMobilSpider(scrapy.Spider):
    name = "exxonmobil"
    allowed_domains = ["exxon.com"]
    start_urls=tuple(urls)

    def parse(self, response):
        json_data = json.loads(response.text)
        for location in json_data:
            self.log(location['WeeklyOperatingDays']+" ######### "+location['WeeklyOperatingHours'])
            properties = {
                "name": location['DisplayName'],
                "addr_full": location['AddressLine1'] +" "+location['AddressLine2'],
                "city": location['City'],
                "state": location['StateProvince'],
                "postcode": location['PostalCode'],
                "phone": location['Telephone'],
                "ref": location['LocationID'],
                "opening_hours": self.store_hours(location['WeeklyOperatingDays']),
                "lat": float(location['Latitude']),
                "lon": float(location['Longitude']),
            }
            logme(GeojsonPointItem(**properties), "geo.txt")
            yield GeojsonPointItem(**properties)

    def store_hours(self, hours):
        hours_list = hours.split("<br/>")
        stripped_hours = [hour for hour in hours_list if hour]
        working_hours = []
        for hour in stripped_hours:
            match = re.search(r"^(\w{2})\w+:(?:(\d+):(\d+)\s(AM|PM)-(\d+):(\d+)\s(AM|PM))?(\w+)?$", hour.strip())
            if match:
                m = match.groups()
                if m[7] is None:
                    # Open hours
                    working_hours.append(
                        m[0] + " " + str(int(m[1]) + self.am_pm(m[1], m[3])).zfill(2) + ":" + m[2] + "-" + str(
                            int(m[4]) + self.am_pm(m[4], m[6])).zfill(2) + ":" + m[5])
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
                    final_working_hours.append(p[0:2] + "-" + hour[0:2] + prev_hours[-12:])
                    prev_hours = hour
                else:
                    # no match, let it be
                    final_working_hours.append(hour)

        if final_working_hours:
            logme("; ".join(final_working_hours), "resultcount.txt")
            return "; ".join(final_working_hours)
        else:
            return hours

    def am_pm(self, hr, a_p):
        """
            A convenience method to fix noon and midnight issues
        :param hr: the hour has to be passed in to accurately decide 12noon and midnight
        :param a_p: this is either a or p i.e am pm
        :return: the hours that must be added
        """
        diff = 0
        if a_p == 'AM':
            if int(hr) < 12:
                diff = 0
            else:
                diff = -12
        else:
            if int(hr) < 12:
                diff = 12
        return diff