import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class VallartaSpider(scrapy.Spider):
    name = "vallarta"
    item_attributes = {"brand": "Vallarta Supermarkets", "brand_wikidata": "Q7911833"}
    allowed_domains = ["vallartasupermarkets.com"]
    download_delay = 0.2
    start_urls = ("https://vallartasupermarkets.com/store-sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            if url == "https://vallartasupermarkets.com/store-locations/":
                continue
            yield scrapy.Request(url=url, callback=self.parse_store, meta={"url": url})

    def parse_store(self, response):
        address = response.xpath("//div[@class='blade store-location']/div/div/div[2]/p[1]/text()").extract()

        # No lat/lon in source code; Google map link contains address
        yield Feature(
            ref=response.url.split("/")[-2],
            name=response.xpath("//div[@class='page-breadcrumb']/span/text()").extract_first(),
            addr_full=address[1].strip(),
            city=address[2].split(",")[0].strip(),
            state=address[2].split(" ")[-2].strip(),
            postcode=address[2].split(" ")[-1].strip(),
            country="United States",
            phone=response.xpath("//a[@class='tel']/text()").extract_first().strip(),
            website=response.url,
            opening_hours=self.parse_hours(
                response.xpath("//div[contains(@class, 'days')]/text()").extract_first().strip(),
                response.xpath("//div[contains(@class, 'hours')]//p/text()").extract_first().strip(),
            ),
        )

    def parse_hours(self, days, hours):
        opening_hours = OpeningHours()

        if "7 Days a Week" in days:
            open_time = hours.split(" - ")[0]
            close_time = hours.split(" - ")[1]

            for day in DAYS:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )
        else:
            return None

        return opening_hours.as_opening_hours()
