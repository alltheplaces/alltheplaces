import json
import re
from urllib.parse import urlparse
import scrapy
from scrapy.selector import Selector

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class GoldsGymSpider(scrapy.Spider):
    name = "goldsgym"
    item_attributes = {"brand": "Gold's Gym", "brand_wikidata": "Q1536234"}
    allowed_domains = ["goldsgym.com"]

    start_urls = [
        "https://www.goldsgym.com/gym_index-sitemap.xml",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for group in hours:
            days, open_time, close_time = re.search(
                r"([a-zA-Z,]+)\s([\d:]+)-([\d:]+)", group
            ).groups()
            days = days.split(",")
            for day in days:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_hotel(self, response):
        if "locate-a-gym" in response.url or "/markets/" in response.url:
            return  # closed gym, redirects

        data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        if data:
            data = json.loads(data)
        else:
            return  # closed gym

        if data.get("@graph"):
            found = False
            for obj in data["@graph"]:
                if obj["@type"] == "ExerciseGym":
                    data = obj
                    found = True
                    break
            if not found:
                return

        properties = {
            "ref": "_".join([x for x in response.url.split("/")[-2:] if x]),
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"].strip(),
            "city": data["address"]["addressLocality"].strip(),
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "phone": data.get("telephone", None),
            "lat": float(data["geo"]["latitude"]),
            "lon": float(data["geo"]["longitude"]),
            "website": response.url,
        }

        hours = self.parse_hours(data["openingHours"])
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        for url in urls:
            path = "/".join(urlparse(url).path.split("/")[:-1])
            yield scrapy.Request(
                response.urljoin(path) + "/", callback=self.parse_hotel
            )
