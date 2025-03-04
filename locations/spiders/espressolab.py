import re

from scrapy import http
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

MAP_SCRIPT_REGEX = re.compile(r"google\.maps\.LatLng\(\s*([-\d.]*)\s*,\s*([-\d.]*)\s*\);")


class EspressolabSpider(CrawlSpider):
    name = "espressolab"
    item_attributes = {"brand": "Espressolab", "brand_wikidata": "Q97599059"}
    allowed_domains = ["espressolab.com"]
    start_urls = ["https://espressolab.com/subeler/"]
    rules = [Rule(LinkExtractor(allow=[r"/subeler/[\w-]+/"]), callback="parse_item")]
    require_proxy = True

    def parse_item(self, response: http.HtmlResponse):
        item = Feature()
        item["ref"] = response.url.split("/")[-2]
        item["name"] = response.xpath("//h1/text()").get()
        item["addr_full"] = merge_address_lines(response.css(".address ::text").getall())
        item["lat"], item["lon"] = map(
            float,
            MAP_SCRIPT_REGEX.search(
                response.xpath("//script[contains(text(), 'google.maps.LatLng')]/text()").get()
            ).groups(),
        )
        yield item
