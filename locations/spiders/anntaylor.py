import scrapy
import re
from locations.items import GeojsonPointItem


class AnntaylorSpider(scrapy.Spider):
    name = "anntaylor"
    item_attributes = {"brand": "Ann Taylor", "brand_wikidata": "Q4766699"}
    allowed_domains = ["stores.anntaylor.com"]
    download_delay = 0
    start_urls = ("https://stores.anntaylor.com/",)

    def parse_stores(self, response):
        ref = re.findall(r"[^(\/)]+$", response.url)
        if len(ref) > 0:
            ref = ref[0].split(".")[0]
        properties = {
            "addr_full": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]/text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
        }
        hours = response.xpath(
            '//div[@class="row"]/div[@class="nap-row-left-col-row-right-hours-of-operation"]/div[@class="c-location-hours-details-wrapper js-location-hours"]/table/tbody/tr/@content'
        ).extract()
        if hours != []:
            hours = " ; ".join(hours)
            properties["opening_hours"] = hours
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath(
            '//h3[@class="Teaser-title Link Link--teaser Heading--h5"]/a/@href'
        ).extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            pattern = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}.html$")
            pattern1 = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if pattern.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif pattern1.match(path.strip()):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(
                    response.urljoin(path), callback=self.parse_city_stores
                )
