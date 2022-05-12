# -*- coding: utf-8 -*-
import re

import scrapy
import json

from locations.items import GeojsonPointItem

countries = (
    "Algeria,DZ",
    "Argentina,AR",
    "Australia,AU",
    "Austria,AT",
    "Azerbaijan,AZ",
    "Belgium,BE",
    "Brazil,BR",
    "Canada,CA",
    "Chile,CL",
    "China,CN",
    "Colombia,CO",
    "Czech Republic,CZ",
    "Denmark,DK",
    "Dominican Republic,DO",
    "Ecuador,EC",
    "Egypt,EG",
    "Finland,FI",
    "France,FR",
    "Germany,DE",
    "Greece,GR",
    "Hungary,HU",
    "India,IN",
    "Indonesia,ID",
    "Ireland,IE",
    "Israel,IL",
    "Italy,IT",
    "Kazakhstan,KZ",
    "Korea,KR",
    "Latvia,LV",
    "Malaysia,MY",
    "Mexico,MX",
    "Morocco,MA",
    "Myanmar,MM",
    "Netherlands,NL",
    "Norway,NO",
    "Panama,PA",
    "Peru,PE",
    "Philippines,PH",
    "Poland,PL",
    "Portugal,PT",
    "Qatar,QA",
    "Romania,RO",
    "Russia,RU",
    "Saudi Arabia,SA",
    "Singapore,SG",
    "South Africa,ZA",
    "Spain,ES",
    "Sweden,SE",
    "Switzerland,CH",
    "Taiwan,TW",
    "Thailand,TH",
    "Tunisia,TN",
    "Turkey,TR",
    "Ukraine,UA",
    "United Arab Emirates,AE",
    "United Kingdom,UK",
    "United States,US",
    "Uzbekistan,UZ",
    "Venezuela,VE",
    "Vietnam,VN",
)


class AlstomSpider(scrapy.Spider):
    # download_delay = 0.3
    name = "alstom"
    item_attributes = {"brand": "Alstom", "brand_wikidata": "Q309084"}
    allowed_domains = ["alstom.com"]
    start_urls = ("https://www.alstom.com/alstom-page/maps/json/1826",)

    def parse(self, response):
        data = json.loads(json.dumps(response.json()))

        for i in data:
            for j in i["locations"]:
                country = i["name"]
                for codes in countries:
                    if codes.split(",")[0] == country:
                        code = codes.split(",")[1]
                try:
                    lng = float(j["long"])
                except:
                    lng = j["long"].replace(",", "").replace(".", "")
                    lng = lng[:3] + "." + lng[3:]
                try:
                    lat = float(j["lat"])
                except:
                    lat = j["lat"].replace(",", "").replace(".", "")
                    lat = lat[:3] + "." + lat[3:]
                try:
                    addr = j["address"]
                    addr_en = addr.encode("ascii", "ignore")
                    addr_de = addr_en.decode()
                    addr = (
                        addr_de.replace("\r\n", "")
                        .replace("<p>", "")
                        .replace("<br />", " ")
                        .replace("</p>", "")
                        .replace("&nbsp;", "")
                    )
                except:
                    addr = j["address"]
                try:
                    t = j["title"]
                    t_en = t.encode("ascii", "ignore")
                    t_de = t_en.decode()
                    title = (
                        t_de.replace("\r\n", "")
                        .replace("<p>", "")
                        .replace("<br />", " ")
                        .replace("</p>", "")
                    )
                except:
                    addr = j["address"]

                properties = {
                    "ref": j["id"],
                    "name": title,
                    "addr_full": addr,
                    "country": code,
                    "phone": j["phone"],
                    "lat": float(lat),
                    "lon": float(lng),
                }

                yield GeojsonPointItem(**properties)
