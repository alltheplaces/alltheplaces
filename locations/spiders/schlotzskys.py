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
        return oh

    def parse(self, response):
        links = response.xpath('//a[@class="Directory-listLink"]')
        for link in links:
            count = link.xpath("./@data-count").get()
            url = response.urljoin(link.xpath("./@href").get().strip())

            if count == "(1)":
                yield scrapy.Request(url, callback=self.parse_store)
            else:
                yield scrapy.Request(url)

    def parse_store(self, response):
        properties = {
            "ref": response.xpath('//main[@id="main"]/@itemid').get(),
            "lat": response.xpath('//meta[@itemprop="latitude"]/@content').get(),
            "lon": response.xpath('//meta[@itemprop="longitude"]/@content').get(),
            "phone": response.xpath('//div[@itemprop="telephone"]/text()').get(),
            "website": response.xpath('//link[@rel="canonical"]/@href').get(),
            "addr_full": response.xpath('//meta[@itemprop="streetAddress"]/text()').get(),
            "city": response.xpath('//meta[@itemprop="addressLocality"]/text()').get(),
            "postcode": response.xpath('//span[@itemprop="postalCode"]/text()').get(),
            "state": response.xpath('//abbr[@itemprop="addressRegion"]/text()').get(),
            "opening_hours": self.parse_hours(response.xpath('//tr[@itemprop="openingHours"]/@content').getall()),
        }

        yield Feature(**properties)
