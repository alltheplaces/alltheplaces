# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class TijuanaFlatsSpider(scrapy.Spider):
    name = "tijuanaflats"
    item_attributes = {"brand": "Tijuana Flats", "brand_wikidata": "Q7801833"}
    allowed_domains = ["tijuanaflats.com"]
    start_urls = ("https://www.tijuanaflats.com/locations",)

    def parse(self, response):
        data = json.loads(
            response.xpath(
                '//tjs-view-locations/attribute::*[name()=":locations"]'
            ).extract_first()
        )
        for row in data:
            for ent in row["yoast_json_ld"][0]["@graph"]:
                if ent["@type"] == "WebPage" and row["slug"] in ent["url"]:
                    name = ent["name"]

            # extract text from html snippet
            hours_of_operation = scrapy.Selector(text=row["acf"]["hours_of_operation"])
            opening_hours = "; ".join(
                a.strip() for a in hours_of_operation.xpath("//text()").extract()
            )

            properties = {
                "ref": row["slug"],
                "name": name,
                "lat": row["acf"]["physical_location"]["lat"],
                "lon": row["acf"]["physical_location"]["lng"],
                "addr_full": row["acf"]["address_1"],
                "city": row["acf"]["city"],
                "state": row["acf"]["state"],
                "postcode": row["acf"]["zip"],
                "phone": row["acf"]["contact_phone"],
                "website": f'https://www.tijuanaflats.com/locations/{row["slug"]}',
                "opening_hours": opening_hours,
            }
            yield GeojsonPointItem(**properties)
