from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MountainEquipmentCompanyCASpider(CrawlSpider, StructuredDataSpider):
    name = "mountain_equipment_company_ca"
    item_attributes = {"brand_wikidata": "Q104867916"}
    start_urls = ["https://www.mec.ca/en/stores"]
    rules = [Rule(LinkExtractor(allow="/en/stores/"), callback="parse_sd")]
