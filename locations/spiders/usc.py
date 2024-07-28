from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class UscSpider(CrawlSpider):
    name = "usc"
    item_attributes = {"brand": "USC", "brand_wikidata": "Q7866331"}
    allowed_domains = ["www.usc.co.uk"]
    start_urls = ["https://www.usc.co.uk/stores/all"]
    rules = [Rule(LinkExtractor(allow=".*-store-.*"), callback="parse", follow=False)]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        if item := LinkedDataParser.parse(response, "LocalBusiness"):
            item["name"] = "USC"
            item["ref"] = response.url
            item["lat"] = response.xpath("//@data-latitude").get()
            item["lon"] = response.xpath("//@data-longitude").get()
            yield item
