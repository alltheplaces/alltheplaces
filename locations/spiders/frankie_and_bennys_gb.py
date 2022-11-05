from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class FrankieAndBennysGBSpider(CrawlSpider, StructuredDataSpider):
    name = "frankie_and_bennys_gb"
    item_attributes = {"brand": "Frankie & Benny's", "brand_wikidata": "Q5490892"}
    allowed_domains = ["www.frankieandbennys.com"]
    start_urls = ["https://www.frankieandbennys.com/restaurants/index.html"]
    rules = [
        Rule(LinkExtractor(allow="/restaurants/"), callback="parse_sd", follow=True)
    ]
    download_delay = 1
    wanted_types = ["Restaurant"]
    search_for_email = False
