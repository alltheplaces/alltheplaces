import re
from datetime import datetime

import scrapy

from locations.categories import Categories
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class WhidbeyCoffeeSpider(scrapy.Spider):
    name = "whidbey_coffee"
    item_attributes = {"brand": "Whidbey Coffee", "extras": Categories.COFFEE_SHOP.value}
    allowed_domains = ["www.whidbeycoffee.com"]
    start_urls = ("https://www.whidbeycoffee.com/sitemap_pages_1.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            yield scrapy.Request(url.strip(), callback=self.parse_store)

    def parse_store(self, response):
        map_link = response.xpath('//div[@itemprop="address"]/p/a/@href').extract_first()
        if not map_link:
            self.logger.info(f"Skipping URL {response.url}")
            return

        lat, lon = re.search(r".*@(-?[\d.]+),(-?[\d.]+).*", map_link).groups()

        yield Feature(
            ref=response.url.split("/")[-1],
            name=response.xpath("//h1/text()").extract_first().strip(),
            lat=float(lat),
            lon=float(lon),
            addr_full=response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first().strip(),
            city=response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first().strip(),
            state=response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first().strip(),
            postcode=response.xpath('//span[@itemprop="postalCode"]/text()').extract_first().strip(),
            phone=response.xpath('//span[@itemprop="telephone"]/text()').extract_first().strip(),
            website=response.url,
            opening_hours=self.parse_hours(response.xpath('//p[strong[contains(text(), "Hours")]]//text()').extract()),
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            if "-" not in hour:
                continue
            if "Drive Thru" in hour or "Cafe" in hour:
                continue

            day_range = hour.split(" ")[0]
            time_range = "".join(hour.split(" ")[1:])
            open_time, close_time = time_range.strip().split("-")

            if ":" not in open_time:
                open_time = datetime.strptime(open_time, "%I%p").strftime("%I:%M%p")
            if ":" not in close_time:
                close_time = datetime.strptime(close_time, "%I%p").strftime("%I:%M%p")

            # Day range, e.g. Mon - Fri
            if "-" in day_range:
                start_day, end_day = re.sub(r"[\s:]", "", day_range).split("-")
                for day in DAYS_3_LETTERS_FROM_SUNDAY[
                    DAYS_3_LETTERS_FROM_SUNDAY.index(start_day[0:3]) : DAYS_3_LETTERS_FROM_SUNDAY.index(end_day[0:3])
                    + 1
                ]:
                    opening_hours.add_range(
                        day=day[0:2],
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%I:%M%p",
                    )
            # Single day, e.g. Sat
            else:
                opening_hours.add_range(
                    day=day_range[0:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )

        return opening_hours.as_opening_hours()
