from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class BarAndBlockGB(CrawlSpider):
    name = "bar_and_block_gb"
    item_attributes = {"brand": "Bar + Block", "brand_wikidata": "Q117599706"}
    start_urls = ["https://www.barandblock.co.uk/en-gb/locations"]
    rules = [Rule(LinkExtractor(allow=r"\/en-gb\/locations\/[-\w]+$"), callback="parse")]
    requires_proxy = True

    def parse(self, response, **kwargs):
        item = Feature()

        item["name"] = response.xpath("//@data-ldname").get()
        item["ref"] = response.xpath("//@data-lid").get()
        item["addr_full"] = clean_address(response.xpath("//address/p/text()").getall())
        item["phone"] = response.xpath('//a[@class="details--table-cell__phone icon__phone"]/text()').get()
        item["email"] = (
            response.xpath('//a[@class="details--table-cell__email icon__email"]/@href').get().replace("mailto:", "")
        )

        extract_google_position(item, response)

        item["website"] = response.url

        return item
