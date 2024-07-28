import scrapy

from locations.items import Feature


class MarcusTheatresSpider(scrapy.Spider):
    name = "marcus_theatres"
    item_attributes = {"brand": "Marcus Theatres", "brand_wikidata": "Q64083352"}
    allowed_domains = ["marcustheatres.com"]
    start_urls = ("http://www.marcustheatres.com/theatre-locations/",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//h3[@class="theatre-name"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                "http://www.marcustheatres.com" + path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            "name": response.xpath('//h1[@class="ph__title text-cursive mb0"]/text()').extract_first(),
            "ref": response.url,
            "addr_full": response.xpath('//div[@class="theatre-map__street-address"]/text()').extract_first(),
            "city": response.xpath('//div[@class="theatre-map__locality"]/text()').extract_first(),
            "state": response.xpath('//div[@class="theatre-map__region"]/text()').extract_first(),
            "postcode": response.xpath('//div[@class="theatre-map__postal-code"]/text()').extract_first(),
            "phone": response.xpath('//div[@class="theatre-map__theatre-phone"]/text()').extract_first(),
            "website": response.url,
            "lat": float(
                response.xpath('//div[@class="map-link"]/a/@href').extract_first().split("loc:")[1].split("+")[0]
            ),
            "lon": float(
                response.xpath('//div[@class="map-link"]/a/@href').extract_first().split("loc:")[1].split("+")[1]
            ),
        }

        yield Feature(**properties)
