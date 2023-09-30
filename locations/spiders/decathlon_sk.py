from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.decathlon_fr import DecathlonFRSpider
from locations.structured_data_spider import StructuredDataSpider


class DecathlonSKSpider(CrawlSpider, StructuredDataSpider):
    name = "decathlon_sk"
    item_attributes = DecathlonFRSpider.item_attributes
    start_urls = ["https://www.decathlon.sk/content/24-nase-predajne-decathlon"]
    rules = [
        Rule(
            LinkExtractor(
                allow="/content/",
                restrict_xpaths=['//div[@class="container-predajne"]/a'],
            ),
            callback="parse_sd",
        )
    ]
    wanted_types = ["SportingGoodsStore"]
