from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TaxAssistGBSpider(CrawlSpider, StructuredDataSpider):
    name = "tax_assist_gb"
    item_attributes = {"brand": "TaxAssist Accountants", "brand_wikidata": "Q122459380"}
    start_urls = ["https://www.taxassist.co.uk/locations"]
    rules = [Rule(LinkExtractor("/accountants/", restrict_xpaths='//div[contains(., "Local Offices")]'), "parse_sd")]
    wanted_types = ["AccountingService"]

    def pre_process_data(self, ld_data, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            if rule["opens"] == "00:00" and rule["closes"] == "00:00":
                rule.pop("opens")

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name")
        yield item
