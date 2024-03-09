from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class NothingBundtCakesUSCASpider(CrawlSpider, StructuredDataSpider):
    name = "nothing_bundt_cakes_us_ca"
    item_attributes = {"brand": "Nothing Bundt Cakes", "brand_wikidata": "Q62082526"}
    allowed_domains = ["www.nothingbundtcakes.com"]
    start_urls = ["https://www.nothingbundtcakes.com/find-a-bakery/"]
    rules = [
        # Example: https://www.nothingbundtcakes.com/find-a-bakery/al/
        Rule(LinkExtractor(allow=r"https://www\.nothingbundtcakes\.com/find-a-bakery/[\w]+/$")),
        # Example: https://www.nothingbundtcakes.com/find-a-bakery/al/madison/
        Rule(LinkExtractor(allow=r"https://www\.nothingbundtcakes\.com/find-a-bakery/[\w]+/[\w]+/$")),
        # Example: https://www.nothingbundtcakes.com/find-a-bakery/mi/okemos/bakery-478.html
        Rule(
            LinkExtractor(allow=r"https://www\.nothingbundtcakes\.com/find-a-bakery/[\w]+/[\w]+/bakery-\d+\.html$"),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["Bakery"]

    def post_process_item(self, item, response, ld_data):
        # Example: 'Weslaco TX Bakery & Cake Shop | Wedding & Birthday Celebration Cakes',
        item["name"] = item["name"].replace(" | Wedding & Birthday Celebration Cakes", "")
        yield item
