import scrapy

from locations.google_url import url_to_coords
from locations.items import Feature


class IntersportSESpider(scrapy.Spider):
    name = "intersport_se"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://www.intersport.se/vara-butiker"]

    def parse(self, response):
        data = response.xpath('//div[@class="store__data"]')
        for location in data:
            item = Feature()
            item["branch"] = location.xpath('.//span[@class="h4-enriched border-bottom"]/text()').get()
            item["addr_full"] = location.xpath('.//div[@class=" store__address mt-5"]/text()').get()
            urls = location.xpath(".//a/@href").getall()
            item["ref"] = item["website"] = "https://www.intersport.se" + urls[0]
            item["lat"], item["lon"] = url_to_coords(urls[1])
            item["phone"] = location.xpath(
                './/span[@class="text-uppercase font-weight-bold border-bottom"]/text()'
            ).get()

            yield item
