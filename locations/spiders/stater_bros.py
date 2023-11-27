import scrapy

from locations.items import Feature


class StaterBrosSpider(scrapy.Spider):
    name = "stater_bros"
    item_attributes = {"brand": "Stater Bros"}
    allowed_domains = ["www.staterbros.com"]

    def start_requests(self):
        urls = [
            "http://www.staterbros.com/store-locator/",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        stores = response.xpath('//div[@class="store"]')
        for index, store in enumerate(stores):
            properties = {
                "addr_full": store.xpath("@data-address").extract_first(),
                "phone": store.xpath('div[@class="left"]/div[@class="phone"]/p/text()').extract()[1],
                "ref": index,
                "lon": store.xpath("@data-longitude").extract_first(),
                "lat": store.xpath("@data-latitude").extract_first(),
                "opening_hours": " ".join(
                    stores[0].xpath('div[@class="right"]/div[@class="hours"]/p/text()').extract()[:2]
                ),
                "name": store.xpath('div[@class="left"]/div[@class="name"]/text()').extract_first(),
            }
            yield Feature(**properties)
