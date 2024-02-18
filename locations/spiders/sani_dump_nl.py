from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.hours import DAYS_NL, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class SaniDumpNLSpider(CrawlSpider, StructuredDataSpider):
    name = "sani_dump_nl"
    item_attributes = {
        "brand": "Sani-Dump",
        "brand_wikidata": "Q123249250",
        "extras": Categories.SHOP_BATHROOM_FURNISHING.value,
    }
    allowed_domains = ["www.sanidump.nl"]
    start_urls = ["https://www.sanidump.nl/winkels/"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.sanidump\.nl\/winkels\/[^/]+\/?$", restrict_xpaths='//a[@class="map-pin"]'
            ),
            callback="parse_sd",
        )
    ]

    def post_process_item(self, item, response, ld_data):
        item["name"] = item["name"].replace("Sani-Dump ", "")
        item.pop("facebook", None)
        hours_string = " ".join(response.xpath('//ul[contains(@class, "opening-hours--regular")]//text()').getall())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_NL)
        yield item
