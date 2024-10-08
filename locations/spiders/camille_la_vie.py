import re

import scrapy

from locations.items import Feature


class CamilleLaVieSpider(scrapy.Spider):
    name = "camille_la_vie"
    item_attributes = {"brand": "Camille La Vie"}
    allowed_domains = ["camillelavie.com"]
    start_urls = ("https://camillelavie.com/locations",)

    def parse(self, response):
        urls = response.xpath('//div[@class="dontsplit"]/div[1]/h3/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)
        coordinates = response.xpath('//td[@valign="top"][2]/a/@href').extract_first()
        lat_lng = re.findall(r"([-]?[\d]+[.][\d]*)", coordinates)

        properties = {
            "ref": ref.strip("/"),
            "addr_full": response.xpath(
                '//table[@class="locations"]/tbody//h3/div/span[2]/span/text()'
            ).extract_first(),
            "city": response.xpath('//table[@class="locations"]/tbody//h3/div/span[3]/text()').extract_first(),
            "state": response.xpath('//table[@class="locations"]/tbody//h3/div/span[4]/text()').extract_first(),
            "postcode": response.xpath('//table[@class="locations"]/tbody//h3/div/span[5]/text()').extract_first(),
            "phone": response.xpath('//table[@class="locations"]/tbody//h3/div/span[6]/span/text()').extract_first(),
            "name": response.xpath('//table[@class="locations"]/tbody//h3/div/span[1]/text()').extract_first(),
            "lat": float(lat_lng[0]),
            "lon": float(lat_lng[1]),
            "website": response.url,
        }

        yield Feature(**properties)
