# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

from urllib.parse import urlencode
import json
from scrapy.selector import Selector


DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su"
}


class SubwaySpider(scrapy.Spider):
    name = "subway"
    item_attributes = { 'brand': "Subway" }
    allowed_domains = ["www.subway.com"]
    download_delay = 2  # limit the delay to 2 seconds to avoid 402 errors

    def start_requests(self):
        url = 'https://locator-svc.subway.com/v3/GetLocations.ashx?'

        with open('./locations/searchable_points/us_centroids_10mile_radius.csv') as points:

            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(',')
                options = {
                    "InputText": "",
                    "Geocode": {
                        "Latitude": lat,

                        "Longitude": lon
                    },
                    "DetectedLocation": {
                        "Latitude": '0',
                        "Longitude": '0',
                        "Accuracy": '0'
                    },
                    "Paging": {
                        "StartIndex": "1",
                        "PageSize": "50"   #max amount
                    },
                    "ConsumerParameters": {
                        "metric": False,
                        "culture": "en-US",
                        "country": "US",
                        "size": "M",
                        "template": "",
                        "rtl": False,
                        "clientId": "17",
                        "key": "SUBWAY_PROD"
                    },
                    "Filters": [],
                    "LocationType": 1,
                    "behavior": "",
                    "FavoriteStores": None,
                    "RecentStores": None
                }

                params = {
                    "q": json.dumps(options)
                }

                yield scrapy.http.Request(url + urlencode(params), self.parse)

    def parse(self, response):
        result = json.loads(response.text[1:-1])
        resultJSON = result['ResultData']
        resultHTML = result['ResultHtml'][2:]

        for i, data in enumerate(resultJSON):
            loc = data['LocationId']
            store_num = loc['StoreNumber']
            address = data['Address']
            html_data = resultHTML[i]  # Access html snippet data, get same index as json data

            properties = {
                "ref": str(store_num) + '-' + str(loc['SatelliteNumber']),  #Unique ID
                "lat": float(data['Geo']['Latitude']),
                "lon": float(data['Geo']['Longitude']),
                "addr_full": address['Address1'],
                "city": address['City'],
                "state": address['StateProvCode'],
                "country": address['CountryCode'],
                "postcode": address['PostalCode'],
                "website": data['OrderingUrl'],
                "phone": Selector(text=html_data).xpath('//div[contains(@class,"locatorPhone")]/text()').extract_first(),
                "opening_hours": self.parse_hours(html_data),
                "extras": {
                    "number": store_num
                }
            }

            yield GeojsonPointItem(**properties)

    def parse_hours(self, data):

        sclass = Selector(text=data)
        days = sclass.xpath('//div[contains(@class,"hoursTable")]//div[contains(@class, "scheduleDay")]//div[contains(@class, "dayName")]/text()').extract()
        start_times = sclass.xpath('//div[contains(@class,"hoursTable")]//div[contains(@class, "scheduleDay")]//div[contains(@class, "openTime")]/text()').extract()
        end_times = sclass.xpath('//div[contains(@class,"hoursTable")]//div[contains(@class, "scheduleDay")]//div[contains(@class, "closeTime")]/text()').extract()

        opening_hours = OpeningHours()
        if '-' in start_times or '-' in end_times:
            return None
        else:
            for day, open_time, close_time in zip(days, start_times, end_times):
                opening_hours.add_range(day=DAY_MAPPING[day], open_time=open_time, close_time=close_time,
                                        time_format="%I:%M %p")
            return opening_hours.as_opening_hours()
