# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PiadaSpider(scrapy.Spider):
    name = "piada"
    item_attributes = {
        "brand": "Piada Italian Street Food",
        "brand_wikidata": "Q7190020",
    }
    start_urls = ["https://mypiada.com/locations"]

    def parse(self, response):
        scr = response.xpath('//script/text()[contains(., "stores.push")]').get()
        for m in re.compile(r"stores\.push\((.*?)\)", re.S).finditer(scr):
            s = m[1]
            s = re.subn(r"^\s+(\w+):", lambda m: f'"{m[1]}":', s, flags=re.M)[0]
            s = s.replace("'", '"')
            s = re.sub(r"marker(Vip)?", "null", s)
            data = json.loads(s)

            lat, lon = data["geo"].split(",")

            addr_full, city_state_zip = (
                scrapy.Selector(text=data["address"]).xpath("//text()").extract()
            )
            city_state = city_state_zip.replace(data["zip"], "").strip()
            city, state = city_state.split(", ")
            phone = scrapy.Selector(text=data["phone"]).xpath("//text()").extract()[1:]
            phone = phone[0].strip() if phone else None
            open_time = data["openTime"]
            close_time = data["closeTime"]

            properties = {
                "ref": data["slug"],
                "lat": lat,
                "lon": lon,
                "website": f'https://mypiada.com/locations/{data["slug"]}',
                "name": data["name"],
                "addr_full": addr_full,
                "city": city,
                "state": state,
                "postcode": data["zip"],
                "phone": phone,
                "opening_hours": f"{open_time}-{close_time}",
            }
            yield GeojsonPointItem(**properties)
