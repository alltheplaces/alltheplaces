from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SallyBeautyCASpider(CrawlSpider, StructuredDataSpider):
    name = "sally_beauty_ca"
    item_attributes = {
        "brand": "Sally Beauty",
        "brand_wikidata": "Q7405065",
    }
    allowed_domains = ["stores.sallybeauty.ca"]
    start_urls = ["https://stores.sallybeauty.ca/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https://stores.sallybeauty.ca/[a-z]{2}/$"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"^https://stores.sallybeauty.ca/[a-z]{2}/[a-z]+/$"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"^https://stores.sallybeauty.ca/[a-z]{2}/[a-z]+/beauty-supply-[\w-]+.html$"),
            callback="parse_sd",
        ),
    ]
    drop_attributes = {"name", "facebook", "image"}
    search_for_twitter = False
