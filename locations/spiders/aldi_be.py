# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

WEEKDAYS = {
    "Ma": "Mo",
    "Di": "Tu",
    "Wo": "We",
    "Do": "Th",
    "Vr": "Fr",
    "Za": "Sa",
    "Zo": "Su",
}


class AldiBESpider(scrapy.Spider):
    name = "aldi_be"
    item_attributes = {"brand": "Aldi"}
    allowed_domains = ["nl.aldi.be"]
    start_urls = ("https://nl.aldi.be/filialen/index/page-1",)

    def parse(self, response):
        stores = response.css(".filtable isloop")
        next = response.css(".filiale .main .row3 a::attr(href)")
        for store in stores:
            data = store.css("tr .td1 .box1")
            website = (
                "https://nl.aldi.be" + data.css("a::attr(href)").extract_first()[1:]
            )
            ref = website.split("/")[-2]
            data = data.css("::text").extract()
            name = data[1]
            street = data[2]
            zipcode, city = re.search(r"(\d+) (.*)", data[3]).groups()
            hours_data = store.css(".openhrs")[0]

            properties = {
                "ref": ref,
                "name": name.strip(),
                "website": website,
                "street": street.strip(),
                "city": city.strip(),
                "postcode": zipcode.strip(),
                "opening_hours": self.hours(hours_data),
            }

            yield GeojsonPointItem(**properties)

        if next:
            yield scrapy.Request(
                "https://nl.aldi.be" + next.extract_first()[1:], callback=self.parse
            )

    def hours(self, data):
        opening_hours = ""
        for item in data.css("tr"):
            item_data = item.css("td::text").extract()
            if "-" in item_data[0]:
                days = item_data[0].split("-")
                f_day = WEEKDAYS[days[0].strip()[:2]]
                t_day = WEEKDAYS[days[1].strip()[:2]]
                day = "{}-{}".format(f_day, t_day)
            else:
                day = WEEKDAYS[item_data[0][:2]]

            opening_hours = opening_hours + "{} {}; ".format(day, item_data[1])

        return opening_hours
