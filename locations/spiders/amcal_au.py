from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.spiders.vapestore_gb import clean_address
from locations.structured_data_spider import StructuredDataSpider


class AmcalAUSpider(CrawlSpider, StructuredDataSpider):
    name = "amcal_au"
    item_attributes = {"brand": "Amcal", "brand_wikidata": "Q63367373"}
    start_urls = ["https://www.amcal.com.au/store-locator"]
    rules = [
        Rule(LinkExtractor(allow=r"/store\-locator/\w{2,3}$")),
        Rule(LinkExtractor(allow=r"/store\-locator/\w{2,3}/\w+"), callback="parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = clean_address(ld_data["address"]["streetAddress"])
        extract_google_position(item, response)

        yield item
