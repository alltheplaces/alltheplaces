import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MyDentistGBSpider(CrawlSpider, StructuredDataSpider):
    MYDENTIST = {"brand": "My Dentist", "brand_wikidata": "Q65118035"}

    name = "mydentist_gb"
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

        # City can come back as eg ["Penistone", "Sheffield"] - put the locality on the end of street address
        if "city" in item and isinstance(item["city"], list):
            item["street_address"] = ", ".join([item["street_address"]] + item["city"][:-1])
            item["city"] = item["city"][-1]

        if item["name"] is not None and (
            item["name"].startswith("mydentist") or item["name"].startswith("{my}dentist")
        ):
            item.update(self.MYDENTIST)
            item["name"] = "{my}dentist"

        yield item
