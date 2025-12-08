from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class NationalWindscreensGBSpider(CrawlSpider, StructuredDataSpider):
    name = "national_windscreens_gb"
    item_attributes = {"brand": "National Windscreens", "brand_wikidata": "Q87142619"}
    allowed_domains = ["nationalwindscreens.co.uk"]
    start_urls = ["https://www.nationalwindscreens.co.uk/fitting-centres"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//div[@class="region"]'), callback="parse_sd")]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("National Windscreens ")
        yield item
