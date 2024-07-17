from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider

OBI_SHARED_ATTRIBUTES = {"brand": "OBI", "brand_wikidata": "Q300518"}


class ObiEUSpider(CrawlSpider, StructuredDataSpider):
    name = "obi_eu"
    item_attributes = OBI_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.obi.at/markt",
        "https://www.obi.ch/markt",
        "https://www.obi.cz/prodejna",
        "https://www.obi.de/markt",
        "https://www.obi.hu/aruhaz",
        "https://www.obi-italia.it/negozio",
        "https://www.obi.pl/stores",
        "https://www.obi.sk/predajna",
    ]
    rules = [
        # Try to avoid complex regex to improve maintainability
        Rule(LinkExtractor(allow=r"https://www.obi.(at|de|ch)/markt/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi.cz/prodejna/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi.sk/predajna/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi-italia.it/negozio/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi.hu/aruhaz/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi.pl/stores/.+", deny="#list"), callback="parse_sd"),
    ]
    download_delay = 0.5
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = ld_data.get("url")
        yield item
