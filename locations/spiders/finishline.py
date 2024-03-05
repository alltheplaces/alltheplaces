from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


# 2024-02-09 - Sitemap excludes Puerto Rico
class FinishlineSpider(CrawlSpider, StructuredDataSpider):
    name = "finishline"
    item_attributes = {"brand": "Finish Line", "brand_wikidata": "Q5450341"}
    allowed_domains = ["stores.finishline.com"]
    start_urls = ["https://stores.finishline.com/browse/"]
    rules = [
        Rule(LinkExtractor(r"com/\w\w/$")),
        Rule(LinkExtractor(r"com/\w\w/[^/]+/$")),
        Rule(LinkExtractor(r"com/\w\w/[^/]+/[^/]+.html$"), "parse"),
    ]
    wanted_types = ["ShoeStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["branch"] = response.xpath("normalize-space(//h2/text())").get()

        yield item
