from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CastoramaPLSpider(CrawlSpider, StructuredDataSpider):
    name = "castorama_pl"
    item_attributes = {"brand": "Castorama", "brand_wikidata": "Q966971"}
    start_urls = ["https://www.castorama.pl/informacje/sklepy"]
    rules = [Rule(LinkExtractor(allow=[r"/sklepy/[-\w]+.html$"]), callback="parse_sd")]
    wanted_types = ["HardwareStore"]
    time_format = "%H:%M:%S Europe/Warsaw"
    search_for_facebook = False
    search_for_email = False

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["image"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "name" in item:
            item["extras"]["web_listing_name"] = item["name"]
        if "brand" in item:
            item["name"] = item["brand"]
        else:
            item["name"] = "Castorama"
        yield item
