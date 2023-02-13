from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class UrbanAirSpider(CrawlSpider, StructuredDataSpider):
    name = "urban_air"
    item_attributes = {"brand": "Urban Air", "brand_wikidata": "Q110172893"}
    start_urls = ["https://www.urbanair.com/locations/"]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/page/\d+/$")),
        Rule(
            LinkExtractor(
                allow=r"https://www.urbanair.com/.+/$",
                restrict_xpaths='//div[@class="wp-block-geodirectory-geodir-widget-loop"]',
            ),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["SportsActivityLocation"]
