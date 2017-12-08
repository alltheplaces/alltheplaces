# -*- coding: utf-8 -*-
"""
https://www.exxon.com/api/v1/Retail/retailstation/GetStationsByBoundingBox?
Latitude1=40.64768480800879&Latitude2=40.77780222218161&
Longitude1=-73.93627828095703&Longitude2=-74.16939443085937


{
"AddressLine1":"309 11TH AVE",
"AddressLine2":"",
"City":"NEW YORK",
"Country":"United States",
"DisplayName":"30TH STREET SERVICE STATION INC",
"LocationID":"309546",
"LocationName":"30THSTREETSERVICESTATIONINC",
"PostalCode":"10001-1213",
"StateProvince":"NY",
"Telephone":"212-594-1515",
"WeeklyOperatingDays":"Open 24 Hours",
"WeeklyOperatingHours":"",
"Latitude":40.7532,
"Longitude":-74.00415,

northeast 47.6604721,-82.5495959
southeast 25.357288, -76.221471
southwest 21.650646, -127.901156
northwest 52.182930, -129.483187

graphically
52.182930, -129.483187              47.6604721,-82.5495959




21.650646, -127.901156              25.357288, -76.221471


"""
import scrapy
import json

from locations.items import GeojsonPointItem


def logme(text, f):
    h=open(f, "a")
    h.write(str(text)+"\n")
    h.close()


max_width=0.9
max_height=0.9


def get_horizontal(start_lat, start_lon, row_width):
    number_of_box = int(abs(row_width) / max_width + 1)  # safe to assume the are left overs
    for box in range(abs(number_of_box)):
        b_lon_left = start_lon
        b_lat_left = start_lat
        # if i subtract 5 from -129, thats -134, we are drifting backwards
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


boxes = []

base_url = 'http://www.exxon.com/api/v1/Retail/retailstation/GetStationsByBoundingBox?'
for row in get_vertical(52, 21):
    for col in get_horizontal(row, -129, -129 + 76):
        boxes.append(base_url + "Latitude1="+str(col[0])+"&Longitude1="+str(col[1])+"&Latitude2="+str(col[2])+"&Longitude2="+str(col[3]))



logme(boxes, "box.txt")



class ExxonMobilSpider(scrapy.Spider):
    name = "exxonmobil"
    allowed_domains = ["www.exxon.com"]
    start_urls=tuple(boxes)
    # start_urls = (
    #     'http://www.exxon.com/api/v1/Retail/retailstation/GetStationsByBoundingBox?'
    #     'Latitude1=40.64768480800879&Latitude2=40.77780222218161&'
    #     'Longitude1=-73.93627828095703&Longitude2=-74.16939443085937',
    # )


    def parse(self, response):
        self.log("#"*50)
        json_data = json.loads(response.text)
        logme(len(json_data), "resultcount.txt")
        for counter, location in enumerate(json_data):
            self.log(location['StateProvince'])
            break
        # This will spider through all the country and regional pages and get us to the individual store pages
        # region_urls = response.xpath('//a[@class="sitemap_link sitemap_bar"]/@href').extract()
        # for url in region_urls:
        #     yield scrapy.Request(url)
        #
        # if response.xpath('//head/meta[@property="og:type"][@content="website"]'):
        #     return
        #
        # # When we get to an individual store page the above for loop won't yield anything
        # # so at this point we're processing an individual store page.
        # contact_props = response.xpath('//head/meta[starts-with(@property, "business:contact_data:")]')
        # contact_info = {}
        # for ele in contact_props:
        #     contact_info[ele.xpath('@property').extract_first()] = ele.xpath('@content').extract_first()
        #
        # properties = {
        #     'phone': contact_info['business:contact_data:phone_number']
        # }
        #
        # address = self.address(contact_info)
        # if address:
        #     properties.update(address)
        #
        # opening_hour_props = response.xpath('//head/meta[starts-with(@property, "business:hours:")]')
        # properties['opening_hours'] = self.store_hours(opening_hour_props)
        #
        # url = response.xpath('//head/link[@rel="canonical"]/@href').extract_first()
        # properties['website'] = url
        #
        # name = response.xpath('//span[@itemprop="legalName"]/text()').extract_first()
        # properties['name'] = name
        #
        # ref = response.url.rsplit('/', 1)[1].split('-', 1)[0]
        # properties['ref'] = ref
        #
        # ll = response.xpath('//div[@itemtype="http://schema.org/GeoCoordinates"]')
        # properties['lon'] = float(ll.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
        # properties['lat'] = float(ll.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),
        #
        # yield GeojsonPointItem(**properties)



    def store_hours(self, store_hours):
        day_groups = []
        hour_iter = iter(store_hours)
        this_day_group = None

        while True:
            try:
                day_elem = hour_iter.next()
            except StopIteration:
                break
            start_elem = hour_iter.next()
            end_elem = hour_iter.next()

            day = day_elem.xpath('@content').extract_first()[:2]
            start_time = start_elem.xpath('@content').extract_first()[:5]
            end_time = end_elem.xpath('@content').extract_first()[:5]

            hours = '{}-{}'.format(start_time, end_time)

            if not this_day_group:
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
            opening_hours = '24/7'
        else:
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
                    opening_hours += '{hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def address(self, address):
        if not address:
            return None

        addr_tags = {
            "addr_full": address['business:contact_data:street_address'],
            "city": address['business:contact_data:locality'],
            "state": address['business:contact_data:region'],
            "postcode": address['business:contact_data:postal_code'],
        }

        return addr_tags