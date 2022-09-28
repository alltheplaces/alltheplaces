from locations.structured_data_spider import StructuredDataSpider

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class FrankieAndBennysSpider(CrawlSpider, StructuredDataSpider):
    name = "frankie_and_bennys"
    item_attributes = {"brand": "Frankie & Benny's", "brand_wikidata": "Q5490892"}
    allowed_domains = ["www.frankieandbennys.com"]
    start_urls = ["https://www.frankieandbennys.com/restaurants/index.html"]
    rules = [
        Rule(LinkExtractor(allow="/restaurants/"), callback="parse_sd", follow=True)
    ]
    download_delay = 1
    wanted_types = ["Restaurant"]
    search_for_email = False
