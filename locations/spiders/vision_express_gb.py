from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class VisionExpressGBSpider(CrawlSpider, StructuredDataSpider):
    name = "vision_express_gb"
    item_attributes = {"brand": "Vision Express", "brand_wikidata": "Q7936150"}
    start_urls = ["https://www.visionexpress.com/store-overview"]
    rules = [
        Rule(LinkExtractor(allow=r"/opticians/[-\w]+$")),
        Rule(LinkExtractor(allow=r"/opticians/[-\w]+/[-\w]+$"), callback="parse_sd"),
    ]
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = item["street_address"].replace(" undefined", "")
        # TODO: when there is an agreed solution to this.
        # if "-tesco" in response.url:
        #    set_located_in(item, "Tesco Extra", "Q25172225")
        extract_google_position(item, response)
        yield item
