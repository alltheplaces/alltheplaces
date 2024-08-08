from scrapy import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.microdata_parser import MicrodataParser, get_object
from locations.structured_data_spider import StructuredDataSpider


def qbd_extract_microdata(doc: Selector):
    return {"items": [get_object(doc.xpath('//*[@itemscope][@itemtype="http://schema.org/Store"]')[0].root)]}


class QbdBooksAUSpider(CrawlSpider, StructuredDataSpider):
    name = "qbd_books_au"
    item_attributes = {"brand": "QBD Books", "brand_wikidata": "Q7270909"}
    allowed_domains = ["www.qbd.com.au"]
    start_urls = ["https://www.qbd.com.au/locations/"]
    rules = [Rule(LinkExtractor(allow=r"^https:\/\/www\.qbd\.com\.au\/locations\/[\w\-]+\/$"), callback="parse_sd")]
    wanted_types = ["Store"]

    def __init__(self):
        MicrodataParser.extract_microdata = qbd_extract_microdata
        super().__init__()

    def post_process_item(self, item, response, ld_data):
        if "www.qbd.com.au" not in item.get("image", ""):
            item.pop("image")
        item.pop("facebook")
        item.pop("twitter")
        yield item
