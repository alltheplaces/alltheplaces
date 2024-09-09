from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ErnestJonesGBSpider(CrawlSpider, StructuredDataSpider):
    name = "ernest_jones_gb"
    item_attributes = {
        "brand": "Ernest Jones",
        "brand_wikidata": "Q5393358",
        "country": "GB",
    }
    allowed_domains = ["www.ernestjones.co.uk"]
    start_urls = ["https://www.ernestjones.co.uk/store-finder/view-stores/GB%20Region"]
    rules = [Rule(LinkExtractor(allow="/store/"), callback="parse", follow=False)]
