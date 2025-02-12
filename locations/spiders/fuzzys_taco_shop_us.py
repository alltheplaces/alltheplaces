import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class FuzzysTacoShopUSSpider(CrawlSpider, StructuredDataSpider):
    name = "fuzzys_taco_shop_us"
    item_attributes = {"brand": "Fuzzy's Taco Shop", "brand_wikidata": "Q85762348"}
    allowed_domains = ["fuzzystacoshop.com"]
    start_urls = ["https://fuzzystacoshop.com/locations/list/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/list/[a-z]{2}/$"),
            callback="parse",
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # POI page url is generated dynamically through javascript code, not available for CrawlSpider.
        for link in set(re.findall(r"onclick=\"window\.open\(\'(.+?)\'", response.text)):
            if "list" in link:  # city page having multiple locations
                yield response.follow(link, callback=self.parse)
            else:  # POI page
                yield response.follow(link, callback=self.parse_sd)
