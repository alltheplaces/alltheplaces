from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

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

    # TODO: Technically, phone is available but not presented in the structured data - ie https://www.kindercare.com/our-centers/brentwood/ca/301830
    # This could be extracted and added
