# -*- coding: utf-8 -*-
import scrapy
import re
import json
from locations.items import GeojsonPointItem

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class AldiESSpider(scrapy.Spider):
    name = "aldi_es"
    item_attributes = {"brand": "Aldi"}
    allowed_domains = ["www.aldi.es"]
    start_urls = ("https://www.aldi.es/encuentra-tu-tienda/",)

    def parse(self, response):
        data = re.search(r"(var dataMap = \{)((.|\s)*?)(}\;)", response.text).groups()
        data = re.search(r"(.*)(\[(.|\s)*\])", data[1]).groups()
        last_occurrence = data[1].rfind(",")
        data = '{}"{}":{}{}'.format(
            "{",
            "stores",
            data[1][:last_occurrence] + data[1][last_occurrence + 1 :],
            "}",
        )
        data = json.loads(data.replace("\\", ""))
        stores = data["stores"]

        for store in stores:
            properties = {
                "ref": store["codigo"],
                "name": store["nombre"],
                "phone": store["telefono"],
                "opening_hours": self.hours(store["horario"]),
                "lat": store["latitude"],
                "lon": store["longitude"],
                "street": store["direccion"],
                "city": store["provincia"],
                "postcode": store["codpostal"],
            }
            yield GeojsonPointItem(**properties)

    def hours(self, data):
        days = data.split(",")
        opening_hours = ""
        for day in days:
            data = day.split(":")
            opening_hours = opening_hours + "{} {}-{};".format(
                WEEKDAYS[int(data[0]) - 2],
                data[1] + ":" + data[2],
                data[3] + ":" + data[4],
            )
        return opening_hours
