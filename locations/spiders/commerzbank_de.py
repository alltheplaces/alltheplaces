# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "mo": "Mo",
    "di": "Tu",
    "mi": "We",
    "do": "Th",
    "fr": "Fr",
    "sa": "Sa",
    "so": "Su",
}


class CommerzbankDESpider(scrapy.Spider):
    name = "commerzbank_de"
    item_attributes = {"brand": "Commerzbank", "brand_wikidata": "Q157617"}
    allowed_domains = ["commerzbank.de"]
    start_urls = ("https://filialsuche.commerzbank.de/de/branch-name",)

    def parse_hours(self, store_info):
        opening_hours = OpeningHours()
        for day in DAY_MAPPING:
            try:
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=store_info[f"{day}MorgenVon"],
                    close_time=store_info[f"{day}MorgenBis"],
                    time_format="%H:%M",
                )
            except KeyError:
                pass
        return opening_hours.as_opening_hours()

    def parse_details(self, response):
        match = re.search(
            r'var decodedResults = JSON.parse\(\$\("<div\/>"\).html\("(\[' r'.*?\])"',
            response.text,
        )
        if match:
            data = match.group(1)
            data = data.encode().decode("unicode-escape")
            data = json.loads(data)

            for branch in data:
                properties = {
                    "name": branch["orgTypName"],
                    "ref": branch["id"],
                    "addr_full": branch["anschriftStrasse"],
                    "city": branch["anschriftOrt"],
                    "postcode": branch["postanschriftPostleitzahl"],
                    "country": "DE",
                    "lat": float(branch["position"][0]),
                    "lon": float(branch["position"][1]),
                    "phone": branch.get("telefon", ""),
                    "extras": {
                        "fax": branch.get("telefax", ""),
                        "email": branch.get("email", ""),
                        "barriere_type": branch.get("barriereTyp", ""),
                        "cash_register": branch.get("kasse", ""),
                        "vault": branch.get("vault", ""),
                        "cashback": branch.get("cashback", ""),
                        "cashgroup": branch.get("cashgroup", ""),
                    },
                }
                hours = self.parse_hours(branch)

                if hours:
                    properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)

    def parse(self, response):
        branches = response.xpath(
            '//div[@class="mainContent"]//a[@class="SitemapLink"]/@href'
        ).getall()

        for branch in branches:
            yield scrapy.Request(url=branch, callback=self.parse_details)
