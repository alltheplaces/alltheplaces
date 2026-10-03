import scrapy

from locations.items import Feature


class MarcusTheatresSpider(scrapy.Spider):
    name = "marcus_theatres"
    item_attributes = {"brand_wikidata": "Q64083352"}
    allowed_domains = ["marcustheatres.com"]
    start_urls = ("http://www.marcustheatres.com/theatre-locations/",)
    requires_proxy = True  # Imperva

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//h3[@class="theatre-name"]/a/@href').getall()
        for path in city_urls:
            yield scrapy.Request(
                "http://www.marcustheatres.com" + path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        properties = {
            "name": response.xpath('//h1[@class="ph__title text-cursive mb0"]/text()').get(),
            "ref": response.url,
            "addr_full": response.xpath('//div[@class="theatre-map__street-address"]/text()').get(),
            "city": response.xpath('//div[@class="theatre-map__locality"]/text()').get(),
            "state": response.xpath('//div[@class="theatre-map__region"]/text()').get(),
            "postcode": response.xpath('//div[@class="theatre-map__postal-code"]/text()').get(),
            "phone": response.xpath('//div[@class="theatre-map__theatre-phone"]/text()').get(),
            "website": response.url,
            "lat": float(response.xpath('//div[@class="map-link"]/a/@href').get().split("loc:")[1].split("+")[0]),
            "lon": float(response.xpath('//div[@class="map-link"]/a/@href').get().split("loc:")[1].split("+")[1]),
        }

        yield Feature(**properties)
