import scrapy
import re
from locations.items import GeojsonPointItem


class JohnLewisSpider(scrapy.Spider):

    name = "johnlewis"
    item_attributes = {"brand": "John Lewis"}
    allowed_domains = ["www.johnlewis.com"]
    download_delay = 0.5
    start_urls = ("https://www.johnlewis.com/our-shops",)

    def parse_stores(self, response):
        location = re.findall(r"[;?]ll=[^(&)]+", response.body_as_unicode())
        addr_full = response.xpath(
            '//div[@class="cq-shop-info"]/p[1]/text()|//div[@id="cq-shop-info"]/p[1]/text()|//div[@id="cq-full-width"]/div[@class="cq-content"]/div/p[@class="shop-address"]/text()'
        ).extract()
        if len(addr_full) > 2:
            city = addr_full[1]
            postcode = addr_full[2]
        else:
            city = addr_full[1].split(",")[0]
            postcode = addr_full[1].split(",")[1]
        if len(location) > 0:
            lat = float(location[0][4:].split(",")[0])
            lon = float(location[0][4:].split(",")[1])
        else:
            lat = ""
            lon = ""
        properties = {
            "addr_full": addr_full[0],
            "phone": response.xpath(
                'normalize-space(//div[@id="cq-shop-info"]/p[@class="impinfo"]/text())'
            ).extract_first(),
            "city": city,
            "state": "",
            "postcode": postcode,
            "ref": response.url,
            "website": response.url,
            "lat": lat,
            "lon": lon,
        }

        # hours = self.parse_hours(response.xpath('//ul[@class="cleanList srHours srSection"]/li'))
        # if hours:
        #     properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath(
            '//section[@class="shop-list"]/div[@class="shop-column"]/div[@class="shop-letter"]/ul/li/a/@href'
        ).extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
