from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider

OBI_SHARED_ATTRIBUTES = {"brand": "OBI", "brand_wikidata": "Q300518"}


class ObiEUSpider(CrawlSpider, StructuredDataSpider):
    name = "obi_eu"
    item_attributes = OBI_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.obi.at/markt/index.html",
        "https://www.obi.ch/markt/index.html",
        "https://www.obi.cz/prodejna/index.html",
        "https://www.obi.de/markt/index.html",
        "https://www.obi.hu/aruhaz/index.html",
        "https://www.obi-italia.it/negozio/index.html",
        "https://www.obi.pl/stores/index.html",
        "https://www.obi.sk/predajna/index.html",
    ]
    rules = [
        # Try to avoid complex regex to improve maintainability
        Rule(LinkExtractor(allow=r"https://www.obi.(at|de|ch)/markt/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi.cz/prodejna/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi.sk/predajna/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi-italia.it/negozio/.+", deny="#list"), callback="parse_sd"),
        Rule(LinkExtractor(allow="https://www.obi.hu/aruhaz/.+", deny="#list"), callback="parse_sd"),
    ]
    download_delay = 0.5

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = ld_data.get("url")
        yield item
