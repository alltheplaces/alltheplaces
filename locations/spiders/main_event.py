import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
import json


class MainEventSpider(scrapy.Spider):
    name = "main_event"
    item_attributes = {
        "brand": "Main Event Entertainment",
        "brand_wikidata": "Q56062981",
    }
    allowed_domains = ["mainevent.com"]
    download_delay = 0.2
    start_urls = ("https://www.mainevent.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            if re.match(r".*/locations/.+$", url):
                yield scrapy.Request(
                    url=url, callback=self.parse_location, meta={"url": url}
                )

    def parse_location(self, response):

        store_data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()

        # Stores pending "Grand Opening" won't have this
        if not store_data:
            return

        store_json = json.loads(store_data)

        # \\"latitude\\":33.318367794546674,\\"longitude\\":-111.74067152513123,
        map_data = response.xpath(
            "//script[contains(text(), 'googleInfo')]/text()"
        ).extract_first()

        yield GeojsonPointItem(
            ref=response.url.split("/")[-2],
            name=store_json["name"],
            lat=re.search('.*latitude\\\\":(-?\d+\.\d+),.*', map_data).group(1),
            lon=re.search('.*longitude\\\\":(-?\d+\.\d+),.*', map_data).group(1),
            addr_full=store_json["address"]["streetAddress"],
            city=store_json["address"]["addressLocality"],
            state=store_json["address"]["addressRegion"],
            postcode=store_json["address"]["postalCode"],
            country=store_json["address"]["addressCountry"],
            phone=store_json["telephone"],
            website=response.url,
            opening_hours=self.parse_hours(store_json["openingHoursSpecification"]),
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for spec in hours:
            if isinstance(spec["dayOfWeek"], list):
                for day in spec["dayOfWeek"]:
                    opening_hours.add_range(
                        day=day[0:2],
                        open_time=spec["opens"],
                        close_time=spec["closes"],
                    )
            else:
                opening_hours.add_range(
                    day=spec["dayOfWeek"][0:2],
                    open_time=spec["opens"],
                    close_time=spec["closes"],
                )

        return opening_hours.as_opening_hours()
