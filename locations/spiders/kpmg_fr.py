# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class KpmgFrSpider(scrapy.Spider):
    name = "kpmg_fr"
    item_attributes = {"brand": "KPMG", "brand_wikidata": "Q493751"}
    allowed_domains = ["home.kpmg"]
    start_urls = [
        "https://home.kpmg/content/kpmgpublic/fr/fr/home/about/offices.regionMap.json",
    ]

    def parse(self, response):
        data = response.json()

        for place in data["Europe"]["France"]:
            yield scrapy.Request(
                url="https://home.kpmg" + place["url"], callback=self.parse_office
            )

    def parse_office(self, response):
        office = response.xpath(
            '//script[@type="text/javascript"]/text()'
        ).extract_first()
        json_data = re.search("kpmgMetaData=(.+?);", office).group(1)
        data = json.loads(json_data)

        properties = {
            "ref": data["KPMG_URL"],
            "name": data["KPMG_Title"],
            "addr_full": data["KPMG_Location_Address_Line_1"],
            "city": data["KPMG_Location_Address_City"],
            "postcode": data["KPMG_Location_Address_Postal_Code"],
            "country": data["KPMG_Location_Country"],
            "lat": data["KPMG_Location_Latitude"],
            "lon": data["KPMG_Location_Longitude"],
            "phone": data["KPMG_Location_Telephone_Number"],
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
