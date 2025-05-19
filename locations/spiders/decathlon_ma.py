from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.decathlon_fr import DecathlonFRSpider
from locations.structured_data_spider import StructuredDataSpider


class DecathlonMASpider(CrawlSpider, StructuredDataSpider):
    name = "decathlon_ma"
    item_attributes = DecathlonFRSpider.item_attributes
    allowed_domains = ["www.decathlon.ma"]
    start_urls = ["https://www.decathlon.ma/content/154-filialen-decathlon"]
    rules = [
        Rule(LinkExtractor(allow=r"/content/\d+-store-"), "parse_sd"),
    ]

    def pre_process_data(self, ld_data: dict, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            for key in ["opens", "closes"]:
                rule[key] = rule.get(key, "").replace("H", ":")
