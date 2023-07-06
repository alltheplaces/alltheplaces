import gzip
import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class GenghisGrillSpider(scrapy.Spider):
    name = "genghis_grill"
    item_attributes = {"brand": "Genghis Grill", "brand_wikidata": "Q29470710"}
    allowed_domains = ["locations.genghisgrill.com"]
    start_urls = ("https://locations.genghisgrill.com/sitemap/sitemap.xml.gz",)

    def parse_store(self, response):
        ref = re.search(r".*-([0-9]+)\.html", response.url).group(1)
        ldjson = response.xpath("//script[@type='application/ld+json']/text()").get()
        data = json.loads(ldjson)[0]
        hours = self.parse_hours(response)

        properties = {
            "ref": ref,
            "name": data["name"].replace("About ", ""),
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "postcode": data["address"]["postalCode"],
            "state": data["address"]["addressRegion"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "phone": data["address"]["telephone"],
            "website": data["url"],
            "opening_hours": hours.as_opening_hours(),
        }

        yield Feature(**properties)

    def parse_hours(self, response):
        opening_hours = OpeningHours()

        hours = response.xpath("//script/text()[contains(., 'Primary Hours')]").extract_first()

        m = re.search(r'"days":(.*]})', hours)
        if not m:
            return
        hours_dict = json.loads(m.group(1))
        for day, times in hours_dict.items():
            if times == "closed":
                continue

            opening_time = times[0]["open"]
            closing_time = times[0]["close"]
            opening_hours.add_range(day[:2], str(opening_time), str(closing_time))

        return opening_hours

    def parse(self, response):
        xml = scrapy.Selector(type="xml", text=gzip.decompress(response.body))
        xml.remove_namespaces()
        urls = xml.xpath("//loc").re(
            r"https:\/\/locations.genghisgrill.com\/[a-z]{2}\/[a-z\-]+\/genghis-grill-[0-9]+\.html"
        )
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)
