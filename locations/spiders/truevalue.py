import html

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class TrueValueSpider(CrawlSpider, StructuredDataSpider):
    name = "truevalue"
    item_attributes = {"brand": "True Value", "brand_wikidata": "Q7847545"}
    start_urls = ["https://stores.truevalue.com"]
    allowed_domains = ["stores.truevalue.com"]
    rules = [
        Rule(LinkExtractor(allow=r"https://stores.truevalue.com/[a-z]{2}/$"), follow=True),
        Rule(LinkExtractor(allow=r"https://stores.truevalue.com/[a-z]{2}/[a-z\-]+/$"), follow=True),
        Rule(LinkExtractor(allow=r"https://stores.truevalue.com/[a-z]{2}/[a-z\-]+/[0-9]+/$"), callback="parse_sd")
    ]
    json_parser = "json5"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = ld_data["@id"]
        item["name"] = html.unescape(item["name"])
        item["street_address"] = html.unescape(item["street_address"])

        oh = OpeningHours()
        oh.from_linked_data(ld_data, "%I:%M %p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
