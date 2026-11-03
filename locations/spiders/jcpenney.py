import json
from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class JcpenneySpider(CrawlSpider, StructuredDataSpider):
    name = "jcpenney"
    item_attributes = {"brand": "JCPenney", "brand_wikidata": "Q920037"}
    allowed_domains = ["jcpenney.com"]
    start_urls = ["https://jcpenney.com/locations/"]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/[-\w]{2}$"), follow=True),
        Rule(LinkExtractor(allow=r"/locations/[-\w]{2}/[-\w]+$"), follow=True),
        Rule(
            LinkExtractor(allow=r"/locations/[-\w]{2}/[-\w]+/clothing-stores-[-\w]+.html$"),
            follow=True,
            callback="parse_sd",
        ),
    ]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    wanted_types = ["Store"]
    requires_proxy = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        for ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := json.loads(ld).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo["latitude"]
                item["lon"] = geo["longitude"]
        item.pop("image", None)
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
