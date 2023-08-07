import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class KrispyKremeSpider(scrapy.Spider):
    name = "krispy_kreme"
    item_attributes = {"brand": "Krispy Kreme", "brand_wikidata": "Q1192805"}
    allowed_domains = ["krispykreme.com"]
    download_delay = 0.2
    start_urls = ("https://www.krispykreme.com/locate/all-locations",)

    def parse(self, response):
        urls = response.xpath("//div[@class='locations']//a/@href").extract()
        for url in urls:
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response):
        yield Feature(
            ref=response.url.split("/")[-1],
            name=response.xpath("//title/text()").extract_first(),
            lat=response.xpath("//meta[@itemprop='latitude']/@content").extract_first(),
            lon=response.xpath("//meta[@itemprop='longitude']/@content").extract_first(),
            street_address=response.xpath("//meta[@itemprop='streetAddress']/@content").extract_first(),
            city=response.xpath("//meta[@itemprop='addressLocality']/@content").extract_first(),
            state=response.xpath("//abbr[@itemprop='addressRegion']/text()").extract_first(),
            postcode=response.xpath("//span[@itemprop='postalCode']/text()").extract_first(),
            country="US",
            phone=response.xpath("//div[@itemprop='telephone']/text()").extract_first(),
            website=response.url,
            opening_hours=self.parse_hours(response.xpath("//tr[@itemprop='openingHours']/@content").extract()),
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour.split(" ")[0]
            times = hour.split(" ")[1]
            if times == "Closed":
                continue
            open_time = times.split("-")[0]
            close_time = times.split("-")[1]

            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()
