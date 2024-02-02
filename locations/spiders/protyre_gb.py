from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ProtyreGBSpider(CrawlSpider, StructuredDataSpider):
    name = "protyre_gb"
    item_attributes = {"brand": "Protyre", "brand_wikidata": "Q7252209"}
    start_urls = ["https://www.protyre.co.uk/garages"]
    rules = [Rule(LinkExtractor(allow="/garages/"), "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        for rule in ld_data.get("openingHoursSpecification", []):
            if rule["opens"] == "00:00" and rule["closes"] == "00:00":
                rule["opens"] = rule["closes"] = None  # Closed, not 24 hours

        ld_data["branchCode"] = None  # Defaults to "0"

        if image := ld_data.get("image", {}).get("url"):
            ld_data["image"]["contentUrl"] = image
