# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class jefferson_univ_hosp(scrapy.Spider):
    name = "jefferson_univ_hosp"
    item_attributes = {
        "brand": "Jefferson University Hospital",
        "brand_wikidata": "Q59676202",
    }
    allowed_domains = ["https://hospitals.jefferson.edu"]
    start_urls = [
        "https://hospitals.jefferson.edu/find-a-location.html",
    ]

    def parse(self, response):
        data = " ".join(
            response.xpath(
                '//script[contains(text(), "itemsArray.push")]/text()'
            ).extract()
        )
        locations = re.findall(r"itemsArray.push\((.+?)\);", data)

        for loc in locations:
            if len(loc.split(";")) == 6:

                loctype, locname, html, url, lat, lon = loc.strip("'").split(";")

                phone = re.search(r"Phone:.*?([\d\-]+?)</p>", html)
                if phone:
                    phone = phone.groups()[0]

                postcode = re.search(r"<br>.+?,.+?(\d{5})</p>", html)
                if postcode:
                    postcode = postcode.groups()[0]

                addr_full = re.search(r"</h3><p>(.+?)<br>", html)
                if addr_full:
                    addr_full = addr_full.groups()[0]

                properties = {
                    "name": locname,
                    "ref": loctype + "_" + locname,
                    "addr_full": addr_full
                    if addr_full
                    else re.search(r"</h3> <p>(.+?)<br>", html).groups()[0],
                    "city": re.search(r"<br>(.+?),", html).groups()[0],
                    "state": re.search(r",(\s\D{2})", html).groups()[0].strip(),
                    "postcode": postcode if postcode else None,
                    "phone": phone if phone else None,
                    "website": url,
                    "lat": float(lat),
                    "lon": float(lon),
                }

            else:
                loctype, html = loc.strip("'").split(";")
                locname, addr_full = html.split("(")

                properties = {"name": locname, "ref": loc, "addr_full": addr_full}

            yield GeojsonPointItem(**properties)
