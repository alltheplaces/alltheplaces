import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class SchlotzskysSpider(scrapy.Spider):
    name = "schlotzskys"
    item_attributes = {"brand": "Schlotzsky's", "brand_wikidata": "Q2244796"}
    allowed_domains = ["schlotzskys.com"]
    start_urls = ["https://locations.schlotzskys.com/"]

    def parse_hours(self, hours):
        oh = OpeningHours()
        for h in hours:
            dow, times = h.split(" ")

            if times == "Closed":
                continue

            open_time, close_time = times.split("-")

            oh.add_range(dow, open_time, close_time)
        return oh.as_opening_hours()

    def parse(self, response):
        links = response.xpath('//a[@class="Directory-listLink"]')
        for link in links:
            count = link.xpath("./@data-count").extract_first()
            url = response.urljoin(link.xpath("./@href").extract_first().strip())

            if count == "(1)":
                yield scrapy.Request(url, callback=self.parse_store)
            else:
                yield scrapy.Request(url)

    def parse_store(self, response):
        properties = {
            "ref": response.xpath('//main[@id="main"]/@itemid').extract_first(),
            "lat": response.xpath('//meta[@itemprop="latitude"]/@content').extract_first(),
            "lon": response.xpath('//meta[@itemprop="longitude"]/@content').extract_first(),
            "phone": response.xpath('//div[@itemprop="telephone"]/text()').extract_first(),
            "website": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            "addr_full": response.xpath('//meta[@itemprop="streetAddress"]/text()').extract_first(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            "opening_hours": self.parse_hours(response.xpath('//tr[@itemprop="openingHours"]/@content').extract()),
        }

        yield Feature(**properties)
