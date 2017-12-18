import scrapy
import re
from locations.items import GeojsonPointItem


class DairyQueenSpider(scrapy.Spider):

    name = "dairyqueen"
    allowed_domains = ["www.dairyqueen.com"]
    download_delay = 1.5
    start_urls = (
        'https://www.dairyqueen.com/us-en/Sitemap/?localechange=1&',
    )

    def parse_stores(self, response):
        google_lnk = response.xpath('//a[@title="Click here to view on Google"]//@href').extract_first()
        matches = re.finditer(r"([-0-9]+\.[0-9]+)", google_lnk)
        if matches:
            lat, lng = [float(next(matches).group(0)) for _ in range(2)]

        properties = {
            'addr_full': response.xpath('//hgroup[@class="store-address"]/h2/text()').extract_first(),
            'phone': response.xpath('//a[@class="telephone-cta"]/text()').extract_first() ,
            'city': response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first(),
            'state': response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
            'ref': response.url,
            'website': response.url,
            'lat': lat,
            'lon': lng
        }
        yield GeojsonPointItem(**properties)

    def parse(self, response):

        stores = response.xpath('(//div[@class="center-960"]/ul/li/a/@href)').extract()

        for store in stores:
            yield scrapy.Request(
                response.urljoin(store),
                callback=self.parse_stores
            )
