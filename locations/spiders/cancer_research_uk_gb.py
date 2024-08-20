from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature


# Sitemap is incomplete - 534 shops but only 218 on sitemap
# No location available
class CancerResearchUkGBSpider(CrawlSpider):
    name = "cancer_research_uk_gb"
    item_attributes = {"brand": "Cancer Research UK", "brand_wikidata": "Q326079"}
    allowed_domains = ["cancerresearchuk.org"]
    start_urls = ["https://www.cancerresearchuk.org/get-involved/find-a-shop"]
    rules = [
        Rule(LinkExtractor(r"/find-a-shop/[^/]+"), callback="parse"),
        Rule(LinkExtractor(r"/find-a-shop\?page=\d+$"), follow=True),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if addr_full := response.xpath('//div[@class="panel-pane pane-custom pane-1 address"]/p/text()').get():
            item = Feature()
            item["addr_full"] = addr_full
            item["postcode"] = addr_full.split(", ")[-1]
            item["country"] = "GB"
            item["ref"] = item["website"] = response.url
            yield item
