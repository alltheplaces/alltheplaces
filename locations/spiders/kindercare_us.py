import urllib

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KindercareUSSpider(CrawlSpider, StructuredDataSpider):
    name = "kindercare_us"
    item_attributes = {
        "brand": "KinderCare Learning Centers",
        "brand_wikidata": "Q6410551",
    }
    allowed_domains = ["kindercare.com"]
    start_urls = [
        "https://www.kindercare.com/our-centers",
    ]
    rules = [
        Rule(
            LinkExtractor(restrict_xpaths=['//div[contains(@class, "link-index-results")]//li']),
            callback="parse_sd",
            follow=True,
        )
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["phone"] = response.xpath('//*[contains(., "Call")]/@href').get().replace("tel:", "")
        if image := item.get("image"):
            item["image"] = urllib.parse.quote(image, safe=":/?=&")
        yield item
