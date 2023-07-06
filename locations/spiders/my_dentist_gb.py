import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MyDentistGBSpider(CrawlSpider, StructuredDataSpider):
    name = "mydentist_gb"
    item_attributes = {
        "brand": "My Dentist",
        "brand_wikidata": "Q65118035",
        "country": "GB",
    }
    allowed_domains = ["mydentist.co.uk"]
    start_urls = ["https://www.mydentist.co.uk/dentists/practices/"]
    rules = [
        Rule(
            link_extractor=LinkExtractor(
                allow=r"https:\/\/www\.mydentist\.co\.uk\/dentists\/practices\/([\w]+)(\/[-\w]+)?(\/[-\w]+)?$",
            ),
        ),
        Rule(
            link_extractor=LinkExtractor(
                allow=r"https:\/\/www\.mydentist\.co\.uk\/dentists\/practices\/([\w]+\/[-\w]+\/[-\w]+\/[-\w]+)$",
            ),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["LocalBusiness"]

    def inspect_item(self, item, response):
        item["lat"] = re.search(r"\"_readModeLat\":(-?[\d.]+),", response.text).group(1)
        item["lon"] = re.search(r"\"_readModeLon\":(-?[\d.]+),", response.text).group(1)

        yield item
