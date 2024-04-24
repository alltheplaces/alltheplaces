import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class AwayResortsSpider(CrawlSpider):
    name = "away_resorts"
    item_attributes = {
        "brand": "Away Resorts",
        "brand_wikidata": "Q108045050",
    }
    start_urls = ["https://www.awayresorts.co.uk/parks/"]
    url_regex = r"https:\/\/www\.awayresorts\.co\.uk\/parks\/([-\w]+)\/([-\w]+)\/$"
    rules = [
        Rule(
            link_extractor=LinkExtractor(
                allow=url_regex,
            ),
            callback="parse_item",
        ),
    ]

    def parse_item(self, response):
        item = LinkedDataParser.parse(response, "Resort")

        if item:
            item["ref"] = re.match(self.url_regex, item["website"]).group(2)

            item["addr_full"] = item["street_address"].replace("\r\n", ", ")
            item["street_address"] = None
            apply_category(Categories.LEISURE_RESORT, item)
            return item
