import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class McalistersDeliSpider(scrapy.Spider):
    name = "mcalisters_deli"
    item_attributes = {"brand": "McAlister's Deli", "brand_wikidata": "Q17020829"}
    allowed_domains = ["locations.mcalistersdeli.com"]
    start_urls = ("https://locations.mcalistersdeli.com/sitemap.xml",)

    def parse_store(self, response):
        if response.url == "https://locations.mcalistersdeli.com/index.html":
            return  # not found, redirects

        ref = re.search(r".*\/([0-9]+[a-z\-]+)", response.url).group(1)
        name = response.xpath("//title/text()").extract_first().split("|")[0]
        addr_full = response.xpath("//meta[@itemprop='streetAddress']/@content").extract_first()
        city = response.xpath("//meta[@itemprop='addressLocality']/@content").extract_first()
        postcode = response.xpath("//span[@itemprop='postalCode']/text()").extract_first()
        geo_region = response.xpath("//meta[@name='geo.region']/@content").extract_first().split("-")
        coordinates = response.xpath("//meta[@name='geo.position']/@content").extract_first().split(";")
        phone = response.xpath("//div[@class='Phone-display Phone-display--withLink']/text()").extract_first()
        hours = self.parse_hours(response)

        properties = {
            "ref": ref,
            "name": name,
            "street_address": addr_full,
            "city": city,
            "postcode": postcode,
            "state": geo_region[1],
            "country": geo_region[0],
            "lat": coordinates[0],
            "lon": coordinates[1],
            "phone": phone,
            "website": response.url,
            "opening_hours": hours.as_opening_hours(),
        }

        yield Feature(**properties)

    def parse_hours(self, response):
        opening_hours = OpeningHours()
        data = response.xpath("//script[@type='text/data' and @class='js-hours-config']/text()").extract_first()

        if not data:
            return opening_hours

        data_dict = json.loads(data)
        for day in data_dict["hours"]:
            day_of_week = day["day"][:2].title()

            if intervals := day["intervals"]:  # If falsy, it's closed on this day
                opening_time = intervals[0]["start"]
                closing_time = intervals[0]["end"]
                opening_hours.add_range(
                    day_of_week,
                    str(opening_time),
                    str(closing_time),
                    time_format="%H%M",
                )

        return opening_hours

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//loc").re(r"https://locations.mcalistersdeli.com\/[a-z]{2}\/[a-z\-]+\/[0-9]+[a-z\-]+")
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)
