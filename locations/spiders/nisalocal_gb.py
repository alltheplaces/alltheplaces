from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class NisaLocalGBSpider(CrawlSpider, StructuredDataSpider):
    name = "nisalocal_gb"
    item_attributes = {"brand": "Nisa", "brand_wikidata": "Q16999069"}
    allowed_domains = ["nisalocally.co.uk"]
    start_urls = ["https://www.nisalocally.co.uk/stores/index.html"]
    rules = [Rule(LinkExtractor(allow=".*/stores/.*"), callback="parse_sd", follow=True)]
    download_delay = 0.5
