import scrapy
import re
from locations.items import GeojsonPointItem


class Haggen(scrapy.Spider):
    name = "haggen"
    item_attributes = {"brand": "Haggen"}
    allowed_domains = ["haggen.com"]
    download_delay = 0.2
    start_urls = ("http://www.haggen.com/find-our-stores/",)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="gmw-results-wrapper gmw-results-wrapper-1 gmw-pt-results-wrapper"]//h2/a/@href'
        ).extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)

    def parse_stores(self, response):

        properties = {
            "addr_full": response.xpath(
                'normalize-space(//div[@class="contactInfo"]/p[1]/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//div[@class="contactInfo"]/text()[3])'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//div[@class="contactInfo"]/p[1]/text()[2])'
            )
            .extract_first()
            .split("\xa0")[0]
            .split(",")[0],
            "state": response.xpath(
                'normalize-space(//div[@class="contactInfo"]/p[1]/text()[2])'
            )
            .extract_first()
            .split("\xa0")[0]
            .split(",")[1],
            "postcode": response.xpath(
                'normalize-space(//div[@class="contactInfo"]/p[1]/text()[2])'
            )
            .extract_first()
            .split("\xa0")[1],
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "website": response.url,
            "name": response.xpath("normalize-space(//main/h2[1]/text())")
            .extract_first()
            .replace("\u2013", ""),
        }

        hours = response.xpath(
            'normalize-space(//div[@class="contactInfo"]/text()[5])'
        ).extract_first()
        if hours == "Open 24 Hours":
            properties["opening_hours"] = "24/7"
        yield GeojsonPointItem(**properties)
