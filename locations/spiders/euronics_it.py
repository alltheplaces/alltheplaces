from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class EuronicsITSpider(CrawlSpider, StructuredDataSpider):
    name = "euronics_it"
    item_attributes = {"brand": "Euronics", "brand_wikidata": "Q184860"}
    start_urls = ["https://www.euronics.it/elenco-negozi-per-regione"]
    rules = [Rule(LinkExtractor(allow=r"/store\?storeId=\d*"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        coords = response.xpath('//*[@id="maincontent"]//span[@class="distance-wrap"]/@data-loc').get()
        item["lat"], item["lon"] = coords.split(",")
        yield item
