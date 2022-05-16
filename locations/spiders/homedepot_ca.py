# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class HomeDepotCanadaSpider(scrapy.Spider):
    name = "homedepot_ca"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["homedepot.ca"]
    start_urls = [
        "https://stores.homedepot.ca/sitemap.xml",
    ]
    download_delay = 0.2

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            if re.match(r"(.*.html)", url):
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        script = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )
        data = script[0]
        ref = re.search(r".+/.+?([0-9]+).html", response.url).group(1)

        properties = {
            "name": data["name"],
            "ref": ref,
            "addr_full": data["address"]["streetAddress"].strip(),
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data.get("address").get("telephone"),
            "website": data.get("url") or response.url,
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
        }

        hours = self.parse_hours(data.get("openingHours"))
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_hours(self, open_hours):
        opening_hours = OpeningHours()
        location_hours = re.findall(r"([a-zA-Z]*)\s(.*?)\s-\s(.*?)\s", open_hours)

        for weekday in location_hours:
            opening_hours.add_range(
                day=weekday[0], open_time=weekday[1], close_time=weekday[2]
            )

        return opening_hours.as_opening_hours()
