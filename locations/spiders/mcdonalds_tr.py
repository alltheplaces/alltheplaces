# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem


class McDonaldsTRSpider(scrapy.Spider):
    name = "mcdonalds_tr"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.com.tr"]

    def start_requests(self):
        url = "https://www.mcdonalds.com.tr/Content/WebService/ClientSiteWebService.asmx/GetRestaurantsV5"
        # for state in STATES:
        formdata = {"cityId": "0", "townId": "0", "Services": ""}

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.mcdonalds.com.tr",
            "Host": "www.mcdonalds.com.tr",
            "Referer": "https://www.mcdonalds.com.tr/kurumsal/restoranlar",
            "X-Requested-With": "XMLHttpRequest",
        }

        yield scrapy.http.Request(
            url,
            self.parse,
            method="POST",
            body=json.dumps(formdata),
            headers=headers,
        )

    def normalize_time(self, time_str):
        match = re.search(r"([0-9]{1,2}):([0-9]{1,2})", time_str)
        h, m = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if int(h) < 13 else int(h),
            int(m),
        )

    def store_hours(self, hour):
        data = hour[0]
        if not data["Name"]:
            return "24/7"
        value = data["Value"].strip()
        if value == "-":
            return None

        start = value.split("-")[0].strip()
        end = value.split("-")[1].strip()
        end = self.normalize_time(end)
        return "Mo-Su " + start + ":" + end

    def parse(self, response):
        results = response.json()
        results = results["d"]
        for data in results:
            properties = {
                "city": data["City"],
                "ref": data["ID"],
                "phone": data["Phone"].strip(),
                "lon": data["Longitude"],
                "lat": data["Latitude"],
                "name": data["Name"],
                "addr_full": data["Address"],
                "state": data["Town"],
            }

            opening_hours = self.store_hours(data["WorkingHours"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
