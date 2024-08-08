import re

import scrapy

from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature


class NormaDESpider(scrapy.Spider):
    name = "norma_de"
    item_attributes = {"brand": "Norma", "brand_wikidata": "Q450180"}
    allowed_domains = ["www.norma-online.de"]

    def start_requests(self):
        url = "https://www.norma-online.de/de/filialfinder/suchergebnis?lng={}&lat={}&r=80000"
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", "DE"):
            yield scrapy.Request(url.format(lon, lat))

    def parse_hours(self, store):
        opening_hours = OpeningHours()
        try:
            weekday = store.xpath(
                './/div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]'
                '//table[@class="shopHours"]//tbody//tr//td/text()'
            )[0].get()
            if weekday:
                from_tm, to_tm = weekday.replace(" ", "").split("-")
                for day in ["Mo", "Tu", "We", "Th", "Fr"]:
                    opening_hours.add_range(
                        day=day,
                        open_time=from_tm.strip(),
                        close_time=to_tm.strip(),
                        time_format="%H:%M",
                    )
        except IndexError:
            pass

        try:
            weekday = store.xpath('.//div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]')[1].get()
            match = re.search(r"Pon.*?: (\d+:\d+) - (\d+:\d+)", weekday)
            if match:
                for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
                    opening_hours.add_range(
                        day=day,
                        open_time=match.group(1).strip(),
                        close_time=match.group(2).strip(),
                        time_format="%H:%M",
                    )
        except IndexError:
            pass

        try:
            saturday = store.xpath(
                './/div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]'
                '//table[@class="shopHours"]//tbody//tr//td/text()'
            )[1].get()
            if saturday:
                from_tm, to_tm = saturday.replace(" ", "").split("-")
                opening_hours.add_range(
                    day="Sa",
                    open_time=from_tm.strip(),
                    close_time=to_tm.strip(),
                    time_format="%H:%M",
                )
        except IndexError:
            pass

        return opening_hours.as_opening_hours()

    def parse(self, response):
        for store in response.xpath('//div[@class="item"]//div[@class="row"]'):
            street = city = zip = lat = lon = ""

            address = store.xpath('.//div[@class="col-xs-12 col-sm-6 col-md-3 col-lg-3"]//p').get()
            match = re.search(r"<p>(.*?)<br>", address)
            if match:
                street = match.group(1)

            match = re.search(r"(\d{5})\s*(.*?)\s*$", address, re.MULTILINE)
            if match:
                zip = match.group(1)
                city = match.group(2)

            position = store.xpath('.//div[@class="col-xs-12 col-sm-6 col-md-2 col-lg-2 actions"]' "//a/@href").get()
            if position:
                match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", position)
                if match:
                    lat = match.group(1)
                    lon = match.group(2)

            properties = {
                "ref": f"{lat}_{lon}",
                "street": street,
                "city": city,
                "postcode": zip,
                "country": "DE",
                "lat": lat,
                "lon": lon,
            }

            hours = self.parse_hours(store)
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)
