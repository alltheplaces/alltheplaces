import html

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class HuboNLSpider(CrawlSpider, StructuredDataSpider):
    name = "hubo_nl"
    item_attributes = {"brand": "Hubo", "brand_wikidata": "Q5473953"}
    start_urls = ["https://www.hubo.nl/winkels"]
    rules = [
        Rule(LinkExtractor(allow=r"https://www\.hubo\.nl/[-\w]+/contact$"), callback="parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = html.unescape(item.pop("name").removeprefix("Hubo "))
        item["city"] = html.unescape(item["city"])
        item["website"] = response.url
        yield item
