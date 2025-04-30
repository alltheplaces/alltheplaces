from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NationalTyresAndAutocareGBSpider(CrawlSpider, StructuredDataSpider):
    name = "national_tyres_and_autocare_gb"
    item_attributes = {"brand": "National Tyres and Autocare", "brand_wikidata": "Q6979055"}
    start_urls = ["https://www.national.co.uk/branches"]
    rules = [
        Rule(
            LinkExtractor(allow=r"branch/(\d+)/[^/]+/$", restrict_xpaths='//a[not(contains(text(), "Halfords"))]'),
            callback="parse",
        )
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("National Tyres and Autocare ")
        extract_google_position(item, response)
        yield item
