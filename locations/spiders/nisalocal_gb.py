from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class NisalocalGBSpider(CrawlSpider, StructuredDataSpider):
    name = "nisalocal_gb"
    item_attributes = {"brand": "Nisa", "brand_wikidata": "Q16999069"}
    allowed_domains = ["nisalocally.co.uk"]
    start_urls = ["https://www.nisalocally.co.uk/stores/index.html"]
    rules = [Rule(LinkExtractor(allow=".*/stores/.*"), callback="parse_sd", follow=True)]
    download_delay = 0.5

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
