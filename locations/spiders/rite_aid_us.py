from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class RiteAidUSSpider(CrawlSpider, StructuredDataSpider):
    name = "rite_aid_us"
    item_attributes = {"brand": "Rite Aid", "brand_wikidata": "Q3433273"}
    start_urls = ["https://www.riteaid.com/locations/index.html"]

    rules = [
        Rule(
            LinkExtractor(allow=r"/\w{2}\.html$"),
        ),
        Rule(LinkExtractor(allow=r"/\w{2}/[^/]+/[^/]+\.html$"), callback="parse_sd", follow=True),
        Rule(LinkExtractor(allow=r"/\w{2}/[^/]+/[^/]+\.html$"), callback="parse_sd"),
    ]
