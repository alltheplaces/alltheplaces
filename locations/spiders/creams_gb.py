from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CreamsGBSpider(CrawlSpider):
    name = "creams_gb"
    item_attributes = {"brand": "Creams", "brand_wikidata": "Q111811895"}
    start_urls = ["https://www.creamscafe.com/our-stores/"]
    rules = [Rule(LinkExtractor(r"/our-stores/[^/]+"), "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.xpath('//div[@class="wpb_wrapper"]/h4/text()').get()
        item["addr_full"] = merge_address_lines(response.xpath('//p[contains(., "Address:")]/text()').getall())
        item["phone"] = response.xpath('//p[contains(., "Telephone:")]/text()').get()
        item["email"] = response.xpath('//p[contains(., "Email:")]/a/text()').get()

        extract_google_position(item, response)

        yield item
