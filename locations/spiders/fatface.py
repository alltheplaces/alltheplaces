from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Request, Rule

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class FatfaceSpider(CrawlSpider):
    name = "fatface"
    item_attributes = {"brand": "FATFACE", "brand_wikidata": "Q5437186"}
    allowed_domains = ["www.fatface.com", "us.fatface.com"]
    start_urls = [
        "https://www.fatface.com/stores",  # GB
        "https://us.fatface.com/stores",  # US and CA
        "https://www.fatface.com/international/stores",  # IE
    ]
    rules = [
        Rule(LinkExtractor(allow="/store/"), callback="parse", follow=False),
        Rule(LinkExtractor(allow="/international/store/"), callback="parse", follow=False),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            if "/international/" in url:
                yield Request(url=url, cookies={"selectedLocale": "en_IE"})
            elif "us.fatface.com" in url:
                yield Request(url=url, cookies={"selectedLocale": "en_US"})
            else:
                yield Request(url)

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        item = LinkedDataParser.parse(response, "Store")
        if item:
            item["ref"] = response.url
            item["name"] = item["name"].strip()
            item["lat"] = response.xpath("//@data-latitude").get()
            item["lon"] = response.xpath("//@data-longitude").get()
            item.pop("image")
            yield item
