import scrapy

from locations.items import Feature


class SoulcycleSpider(scrapy.Spider):
    name = "soulcycle"
    item_attributes = {"brand": "Soulcycle", "brand_wikidata": "Q17084730"}
    allowed_domains = ["soul-cycle.com"]
    start_urls = ("https://www.soul-cycle.com/studios/all/",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//div[@class="open-modal studio-detail"]/@data-url').extract()
        for path in city_urls:
            yield scrapy.Request(
                "https://www.soul-cycle.com" + path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            "name": response.xpath('//*[@class="studio-name"]/@data-studio-name').extract_first(),
            "ref": response.xpath('//*[@class="studio-name"]/@data-studio-name').extract_first(),
            "addr_full": response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
            "city": response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            "state": response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            "postcode": response.xpath('//span[@itemprop="address"]/text()').extract()[3],
            "phone": response.xpath('//a[@itemprop="telephone"]/text()').extract_first(),
            "website": response.request.url,
            "lat": response.xpath("//div[@class]/div[@class]/script")
            .extract()[-1]
            .split("LatLng(")[1]
            .split(")")[0]
            .split(",")[0],
            "lon": response.xpath("//div[@class]/div[@class]/script")
            .extract()[-1]
            .split("LatLng(")[1]
            .split(")")[0]
            .split(",")[1],
        }

        yield Feature(**properties)
