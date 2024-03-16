import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class GraingerUSSpider(CrawlSpider):
    name = "grainger_us"
    item_attributes = {"brand": "Grainger", "brand_wikidata": "Q1627894"}
    start_urls = ["https://www.grainger.com/content/find-branch-location"]
    rules = [Rule(LinkExtractor("/branch/"), callback="parse")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    user_agent = BROWSER_DEFAULT

    def parse(self, response, **kwargs):
        item = Feature()
        item["website"] = response.xpath('//link[@rel="canonical"]/@href').get()
        item["lat"] = response.xpath("//@data-default-latitude").get()
        item["lon"] = response.xpath("//@data-default-longitude").get()
        item["branch"], item["ref"] = (
            response.xpath('//h1[@class="branch-info__heading"]/text()').get().split(" Branch #")
        )
        item["addr_full"] = merge_address_lines(response.xpath('//*[@class="branch-info__address"]/text()').getall())
        if m := re.search(r", (\w\w) ([-\d]+)$", item["addr_full"]):
            item["state"], item["postcode"] = m.groups()

        yield item
