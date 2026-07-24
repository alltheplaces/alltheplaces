from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class VillageInnSpider(CrawlSpider, StructuredDataSpider):
    name = "village_inn"
    item_attributes = {"brand": "Village Inn", "brand_wikidata": "Q7930659"}
    # allowed_domains = ["www.villageinn.com"]
    start_urls = ("https://www.villageinn.com/Locations",)
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//*[@id="state-list"]')),
        Rule(LinkExtractor(restrict_xpaths='//*[@id="storeListContainer"]'), callback="parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Village Inn - ", "")
        oh = OpeningHours()
        oh.add_ranges_from_string(ld_data.get("openingHours"))
        item["opening_hours"] = oh
        yield item
