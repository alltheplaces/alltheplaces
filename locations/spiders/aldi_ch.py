# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem


class AldiCHSpider(scrapy.Spider):
    name = "aldi_ch"
    item_attributes = {"brand": "Aldi", "brand_wikidata": "Q41171672"}
    allowed_domains = ["www.yellowmap.de"]
    start_urls = (
        "https://www.yellowmap.de/Presentation/AldiSued/de-CH/ResultList?LocX=&LocY=&HiddenBranchCode=&BranchCode=&Lux=6.2841796875&Luy=49.24629332459796&Rlx=10.755615234375&Rly=44.59829048984011&ZoomLevel=4",
    )

    def parse(self, response):
        data = response.json()
        container = data["Container"]
        stores = self.parse_data(container)

        for store in stores:
            json_data = json.loads(
                store.css(".resultItem::attr(data-json)").extract_first()
            )
            ref = json_data["id"]
            lat = json_data["locY"]
            lon = json_data["locX"]
            name = store.css(".resultItem-CompanyName::text").extract_first()
            street = store.css(".resultItem-Street::text").extract_first()
            address1 = store.css(".resultItem-City::text").extract_first().split(",")
            hours_data = store.css(".openingHoursTable > tr")

            (zipcode, city) = re.search(r"(\d+)(.*)", address1[0]).groups()

            properties = {
                "ref": ref,
                "name": name,
                "opening_hours": self.hours(hours_data),
                "lat": lat,
                "lon": lon,
                "street": street.strip(),
                "city": city,
                "postcode": zipcode.strip(),
            }

            yield GeojsonPointItem(**properties)

        if "zoom" in response.meta.keys():
            zoom = response.meta["zoom"]
        else:
            zoom = 5

        for child in self.children(container):
            yield scrapy.Request(
                "https://www.yellowmap.de/Presentation/AldiSued/de-CH/ResultList?LocX={}&LocY={}&ZoomLevel={}".format(
                    child["locX"], child["locY"], zoom
                ),
                meta={"zoom": zoom + 1},
                callback=self.parse,
            )

    def children(self, data):
        json_data = re.search(r"Tiles:\s+(\[{.*}\])", data)
        if json_data:
            return json.loads(json_data.groups()[0])
        else:
            return []

    def parse_data(self, data):
        data = scrapy.http.HtmlResponse(url="", body=data, encoding="utf-8")
        stores = data.css(".resultItem")
        if stores:
            return stores
        else:
            return []

    def hours(self, data):
        opening_hours = ""
        for day_group in data:
            time = day_group.css("td::text").extract()
            day = time[0].strip()
            hours = time[1].strip()

            if "-" in day:
                f_day = day.split("-")[0].strip()[:2]
                t_day = day.split("-")[1].strip()[:2]
                day = "{}-{}".format(f_day, t_day)
            else:
                day = day[:2]
            if hours == "geschlossen":
                opening_hours += "{} {};".format(day, "closed")
            else:
                f_hour_text = hours.split("-")[0].strip()
                t_hour_text = hours.split("-")[1].strip()
                f_hour = self.normalize_time(f_hour_text)
                t_hour = self.normalize_time(t_hour_text)
                opening_hours += "{} {}; ".format(day, "{}-{}".format(f_hour, t_hour))

        return opening_hours

    def normalize_time(self, time_str):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2})", time_str)
        if not match:
            h = re.search(r"([0-9]{1,2})", time_str).group()
            m = "0"
        else:
            h, m = match.groups()

        return "%02d:%02d" % (
            int(h),
            int(m),
        )
