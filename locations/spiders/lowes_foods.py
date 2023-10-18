import re

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class LowesFoodsSpider(scrapy.Spider):
    name = "lowes_foods"
    item_attributes = {"brand": "Lowes Foods", "brand_wikidata": "Q6693991"}
    allowed_domains = ["lowesfoods.com"]
    download_delay = 0.2
    start_urls = ("https://www.lowesfoods.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            if re.match(r".*store-locator/store-\d+$", url):
                yield scrapy.Request(url=url, callback=self.parse_store, meta={"url": url})

    def parse_store(self, response):
        city_state_zip = (
            response.xpath("//div[@class='store-details__store-info']/ul/li[4]/text()").extract_first().strip()
        )

        map_data = response.xpath('//script[contains(text(), "initMap")]').extract_first()

        yield Feature(
            ref=response.url.split("/")[-1],
            name=response.xpath("//div[@class='store-details__heading']/h1/text()").extract_first().strip(),
            lat=re.search(r".*lat: (-?\d+\.\d+),.*", map_data).group(1),
            lon=re.search(r".*lng: (-?\d+\.\d+).*", map_data).group(1),
            street_address=response.xpath("//div[@class='store-details__store-info']/ul/li[2]/text()")
            .extract_first()
            .strip(),
            city=city_state_zip.split(",")[0],
            state=city_state_zip.split(" ")[1],
            postcode=city_state_zip.split(" ")[2],
            country="United States",
            phone=response.xpath("//div[@class='store-details__store-info__phone']/a/text()").extract_first().strip(),
            website=response.url,
            opening_hours=self.parse_hours(
                response.xpath("//div[@class='store-details__heading']/h2/text()").extract_first().strip()
            ),
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        if "Daily" in hours:
            open_time = hours.split(" - ")[0].split(" ")[-1]
            close_time = hours.split(" - ")[1]
            # There is sometimes a space between the time and 'PM'
            close_time = "".join(close_time.split(" "))

            for DAY in DAYS:
                opening_hours.add_range(
                    day=DAY,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )
        else:
            return None

        return opening_hours.as_opening_hours()
