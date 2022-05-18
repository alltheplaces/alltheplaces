import scrapy
import re
from locations.items import GeojsonPointItem


class MichaelkorsSpider(scrapy.Spider):

    name = "michaelkors"
    item_attributes = {"brand": "Michael Kors", "brand_wikidata": "Q19572998"}
    allowed_domains = ["locations.michaelkors.com"]
    download_delay = 0.5
    start_urls = ("https://locations.michaelkors.com/index.html",)

    def parse_stores(self, response):
        ref = re.findall(r"[^(\/)]+$", response.url)
        if len(ref) > 0:
            ref = ref[0].split(".")[0]
        properties = {
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/text())'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//abbr[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "country": response.xpath(
                '//abbr[@itemprop="addressCountry"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(
                response.xpath(
                    'normalize-space(//meta[@itemprop="latitude"]/@content)'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    'normalize-space(//meta[@itemprop="longitude"]/@content)'
                ).extract_first()
            ),
        }
        hours = response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
        if hours != []:
            hours = "; ".join(hours)
            properties["opening_hours"] = hours
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//a[@class="LocationCard-storeLink"]/@href').extract()
        if stores == []:
            yield scrapy.Request(response.url, callback=self.parse_stores)
        else:
            for store in stores:
                yield scrapy.Request(
                    response.urljoin(store), callback=self.parse_stores
                )

    def parse_state(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            path_split = len(path.split("/"))
            if path_split == 4:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)

    def parse_country(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            path_split = len(path.split("/"))
            if path_split == 2:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif path_split == 3:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            path_split = len(path.split("/"))
            if path_split == 1:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_country
                )
            elif path_split == 2:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif path_split == 3:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
