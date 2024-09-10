from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import PaymentMethods, map_payment
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider

SPUR_COUNTRIES = [
    "au",
    "bw",
    "ke",
    "mu",
    "na",
    "ng",
    "sz",
    "za",
    "zm",
    "zw",
]

# CrawlSpider rather than sitemap because the sitemap only had ZA locations, not other countries


class SpurSpider(CrawlSpider, StructuredDataSpider):
    name = "spur"
    item_attributes = {"brand": "Spur", "brand_wikidata": "Q7581546"}
    start_urls = [f"https://www.spursteakranches.com/{cc}/find-a-spur" for cc in SPUR_COUNTRIES]
    base_url = "https://www.spursteakranches.com"
    allowed_domains = ["spursteakranches.com"]
    rules = [
        Rule(LinkExtractor(allow=r"spursteakranches.com/\w\w/find-a-spur\?page=\d+")),
        Rule(LinkExtractor(allow=r"spursteakranches.com/\w\w/restaurant/[\/\-\w()]+$"), callback="parse"),
    ]
    search_for_facebook = False
    search_for_twitter = False

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            yield ld_obj["mainEntity"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = None
        if item["state"] == "International":
            item.pop("state")

        payments = ld_data["paymentAccepted"][0].split(", ")
        for payment in payments:
            if not map_payment(item, payment, PaymentMethods):
                self.crawler.stats.inc_value(f"atp/{self.name}/payment/fail/{payment}")

        yield item
