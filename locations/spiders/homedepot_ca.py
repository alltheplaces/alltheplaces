# -*- coding: utf-8 -*-
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from scrapy.spiders import SitemapSpider


class HomeDepotCanadaSpider(SitemapSpider):
    name = "homedepot_ca"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["homedepot.ca"]
    download_delay = 0.2
    sitemap_urls = ["https://stores.homedepot.ca/sitemap.xml"]
    sitemap_rules = [
        (
            "https:\/\/stores\.homedepot\.ca\/([\w]{2})\/([-\w]+)\/([-\w]+)([\d]+)\.html$",
            "parse_store",
        ),
    ]

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
            "street_address": data["address"]["streetAddress"].strip(),
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
