import re

import scrapy

from locations.categories import Categories
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature


class CanadaPostSpider(scrapy.Spider):
    name = "canada_post"
    item_attributes = {"brand": "Canada Post", "brand_wikidata": "Q1032001", "extras": Categories.POST_OFFICE.value}
    allowed_domains = ["canadapost-postescanada.ca"]

    def start_requests(self):
        url = (
            "https://www.canadapost-postescanada.ca/information/app/fpo/personal/findpostofficelist?lat={lat}&lng={lon}"
        )
        for lat, lon in point_locations("ca_centroids_25mile_radius_territory.csv"):
            yield scrapy.Request(url.format(lat=lat, lon=lon), callback=self.parse_list)

    def parse_list(self, response):
        urls = response.xpath('//a[contains(@href,"outletId")]/@href')
        for url in urls:
            yield scrapy.Request(url=f"https://www.{self.allowed_domains[0]}{url.get()}", callback=self.parse_office)

    def parse_office(self, response):
        address = response.xpath('//div[@id="results"]//address/p[1]/text()[3]').get()
        state = re.findall("[A-Z]{2}", address)[0]
        postcode = re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", address)[0]
        city = address.replace(state, "").replace(postcode, "").strip().replace(",", "")

        oh = OpeningHours()
        days = response.xpath('//div[@id="hoursOperation"]//tr')
        for day in days:
            if day.xpath("./td[2]/text()").get() == " - ":
                continue
            hours = day.xpath("./td[2]/text()").get()
            if len(re.findall("-", hours)) == 1:
                oh.add_range(
                    day=day.xpath("./td[1]/text()").get(),
                    open_time=hours.split(" - ")[0],
                    close_time=hours.split(" - ")[1],
                )
                continue
            for hour in hours.split(" - "):
                oh.add_range(
                    day=day.xpath("./td[1]/text()").get(),
                    open_time=hour.split("-")[0],
                    close_time=hour.split("-")[1],
                )

        properties = {
            "ref": re.findall("[0-9]+", response.url)[0],
            "name": response.xpath('//div[@id="results"]//address/p[1]/text()[1]').get(),
            "street_address": response.xpath('//div[@id="results"]//address/p[1]/text()[2]').get().strip("\n").strip(),
            "city": city,
            "state": state,
            "postcode": postcode,
            "lat": response.xpath('//input[@id="fpoDetailForm:latitude"]/@value').get(),
            "lon": response.xpath('//input[@id="fpoDetailForm:longitude"]/@value').get(),
            "website": response.url,
            "opening_hours": oh.as_opening_hours(),
        }

        yield Feature(**properties)
