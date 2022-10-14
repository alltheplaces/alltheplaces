import json
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours, DAYS


class GelsonsSpider(scrapy.Spider):
    name = "gelsons"
    item_attributes = {"brand": "Gelson's Markets", "brand_wikidata": "Q16993993"}
    allowed_domains = ["gelsons.com"]
    download_delay = 0.2
    start_urls = ("https://www.gelsons.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            if re.match(r".*stores/.+$", url) and "virtual" not in url:

                yield scrapy.Request(
                    url=url, callback=self.parse_store, meta={"url": url}
                )

    def parse_store(self, response):

        content = json.loads(
            response.xpath('//script[@type="application/json"]/text()').extract_first()
        )["props"]["pageProps"]
        store_json = content["store"]
        hours = content["pageComponents"][0]["headline"]

        yield GeojsonPointItem(
            ref=store_json["slug"],
            name=store_json["title"],
            lat=store_json["lat"],
            lon=store_json["long"],
            addr_full=store_json["address"],
            city=store_json["city"],
            state="CA",
            postcode=store_json["zipCode"],
            country="US",
            phone=store_json["storePhone"],
            website=response.url,
            opening_hours=self.parse_hours(hours),
        )

    def parse_hours(self, hour_string):
        """Hours look like one of the following:

        Hours: 7am - 9pm, 7 days a week
        Hours: 7am - 9:30pm, 7 days a week

        """
        hours = OpeningHours()
        open_time = hour_string.split(": ")[1].split(" - ")[0].replace(" ", "")
        close_time = hour_string.split(" - ")[1].split(",")[0].replace(" ", "")

        # Add minutes, if necessary
        if ":" not in open_time:
            open_time = f"{open_time[:-2]}:00am"

        if ":" not in close_time:
            close_time = f"{close_time[:-2]}:00pm"

        if "7 days a week" in hour_string:
            for day in DAYS:
                hours.add_range(day, open_time, close_time, time_format="%H:%M%p")

        return hours.as_opening_hours()
