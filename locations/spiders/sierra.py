import scrapy

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SierraSpider(StructuredDataSpider):
    name = "sierra"
    item_attributes = {"brand": "Sierra Trading Post", "brand_wikidata": "Q7511598"}
    allowed_domains = ["sierra.com"]
    start_urls = ["https://www.sierra.com/lp2/retail-stores/"]
    wanted_types = ["LocalBusiness"]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def parse(self, response):
        for url in response.xpath('//div[@class="m-b"]/a [contains(., "Store Info and Directions")]/@href').extract():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
