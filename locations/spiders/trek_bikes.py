import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class TrekBikesSpider(scrapy.Spider):
    name = "trek_bikes"
    allowed_domains = ["www.trekbikes.com"]
    start_urls = ["https://www.trekbikes.com/store-finder/allRetailers/"]

    def parse(self, response):
        if "var storeDescription" in response.text:
            yield from self.parse_store(response)
        yield from response.follow_all(css="a.country__link")
        yield from response.follow_all(css="a.pagination__button")

    def parse_store(self, response):
        script = response.xpath('//*[@type="text/javascript"]/text()[contains(.,"var store")]').get()
        data = {}
        for key, val1, val2 in re.findall(r"var (store\w+) = (?:'(.*)'|\"(.*)\");$", script, flags=re.M):
            data[key] = val1 or val2

        opening_hours = OpeningHours()
        hours_table = response.xpath('//table[@qaid="store-hours"]')
        for row in hours_table.xpath(".//tr"):
            s = row.xpath(".//text()").extract()
            day, *intervals = (x.strip() for x in s if x.strip())
            for interval in intervals:
                if interval == "Closed":
                    continue
                open_time, close_time = interval.split("-")
                opening_hours.add_range(day[:2], open_time, close_time, "%I:%M %p")

        phone = response.xpath('//@href[contains(.,"tel:")]').get()
        phone = phone is None or phone.lstrip("tel:")

        lat = data["storelatitude"]
        lon = data["storelongitude"]
        if (lat, lon) == ("0.0", "0.0"):
            lat, lon = None, None

        properties = {
            "ref": response.url,
            "name": data["storeDescription"],
            "lat": lat,
            "lon": lon,
            "street_address": data["storeaddressline1"],
            "city": data["storeaddresstown"],
            "postcode": data["storeaddresspostalCode"],
            "country": data["storeaddresscountryname"],
            "opening_hours": opening_hours.as_opening_hours(),
            "website": response.xpath('//*[contains(.,"Retailer website")]/@href').get(response.url),
            "phone": phone,
        }

        if "embedsocial" in response.text:
            properties.update({"brand": "Trek", "brand_wikidata": "Q1067617"})

        yield Feature(**properties)
