from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class YoursclothingGBSpider(CrawlSpider, StructuredDataSpider):
    name = "yoursclothing_gb"
    item_attributes = {"brand": "Yours Clothing", "brand_wikidata": "Q84163322"}
    allowed_domains = ["yoursclothing.co.uk"]
    start_urls = ["https://www.yoursclothing.co.uk/store-finder"]
    rules = [Rule(LinkExtractor(allow="/store-finder/"), callback="parse_sd")]
    wanted_types = ["Store"]
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = ld_data["address"]["name"].removesuffix(" Store")
        item["lat"] = response.xpath("//@data-startlat").get()
        item["lon"] = response.xpath("//@data-startlong").get()

        yield item
