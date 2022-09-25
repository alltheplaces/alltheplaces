from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from locations.google_url import url_to_coords
from locations.items import GeojsonPointItem


class BarAndBlockGB(CrawlSpider):
    name = "bar_and_block_gb"
    item_attributes = {"brand": "Bar and Block"}
    start_urls = ["https://www.barandblock.co.uk/en-gb/locations"]
    rules = [
        Rule(LinkExtractor(allow=r"\/en-gb\/locations\/[-\w]+$"), callback="parse")
    ]

    def parse(self, response, **kwargs):
        item = GeojsonPointItem()

        item["name"] = response.xpath("//@data-ldname").get()
        item["ref"] = response.xpath("//@data-lid").get()

        item["addr_full"] = ", ".join(
            filter(None, map(str.strip, response.xpath("//address/p/text()").getall()))
        )

        item["phone"] = response.xpath(
            '//a[@class="details--table-cell__phone icon__phone"]/text()'
        ).get()
        item["email"] = (
            response.xpath('//a[@class="details--table-cell__email icon__email"]/@href')
            .get()
            .replace("mailto:", "")
        )

        item["lat"], item["lon"] = url_to_coords(
            response.xpath(
                '//a[@class="details--table-cell__directions icon__directions"]/@href'
            ).get()
        )

        item["website"] = response.url

        item["country"] = "GB"

        return item
