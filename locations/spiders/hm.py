import scrapy
from locations.items import GeojsonPointItem
import json
import requests


def process_hours(opening_hours):
    ret_hours = []
    for hours_str in opening_hours:
        split_hours = hours_str.split(" ")
        if split_hours.count("-") == 2 and split_hours[1] == "-":
            range_start, _, range_end, start, start_period, _, end, end_period = split_hours
            start_hour, start_minutes = [int(x) for x in start.split(":")]
            end_hour, end_minutes = [int(x) for x in end.split(":")]

            if start_period == "PM":
                start_hour += 12
            end_hour += 12
            hours = (range_start[:2], range_end[:2], start_hour, start_minutes, end_hour, end_minutes)
            ret_hours.append("%s-%s %02d:%02d-%02d:%02d" % hours)
        else:
            day, start, start_period, _, end, end_period = split_hours
            start_hour, start_minutes = [int(x) for x in start.split(":")]
            end_hour, end_minutes = [int(x) for x in end.split(":")]
            if start_period == "PM":
                start_hour += 12
            end_hour += 12
            hours = (day[:2], start_hour, start_minutes, end_hour, end_minutes)
            ret_hours.append("%s %02d:%02d-%02d:%02d" % hours)
    return "; ".join(ret_hours)

class HMSpider(scrapy.Spider):
    name = "hm-worldwide"
    all_stores_uri = 'https://hm.storelocator.hm.com/rest/storelocator/stores/1.0/locale/en_US/country/{}/'
    start_urls = ["http://www.hm.com/entrance.ahtml"]

    def parse(self, response):
        country_urls = response.css(".column li a::attr('href')").extract()
        country_codes = {x.split("=")[1].split("&")[0].upper() for x in country_urls}
        for country_code in country_codes:
            yield scrapy.Request(url=self.all_stores_uri.format(country_code), callback=self.parse_country)

    def parse_country(self, response):
        stores = response.css("storeComplete")
        for store in stores:
            point = {
                "lat": store.xpath("latitude/text()").extract_first(),
                "lon": store.xpath("longitude/text()").extract_first(),
                "name": store.xpath("name/text()").extract_first(),
                "addr_full": store.xpath("address/addressLine/text()").extract_first(),
                "city": store.xpath("city/text()").extract_first(),
                "country": store.xpath("country/text()").extract_first(),
                "phone": store.xpath("phone/text()").extract_first(),
                "opening_hours": process_hours(store.xpath("openingHours/openingHour/text()").extract()),
                "ref": store.xpath("storeId/text()").extract_first()
            }
            if "/country/US" in response.url:
                point["state"] = store.xpath("region/name/text()").extract_first()
                point["postcode"] = store.xpath("address/addressLine/text()").extract()[-1].split(" ")[-1]

            yield GeojsonPointItem(**point)
