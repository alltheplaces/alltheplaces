import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CrewClothingGBSpider(CrawlSpider, StructuredDataSpider):
    name = "crew_clothing_gb"
    item_attributes = {"brand": "Crew Clothing Company", "brand_wikidata": "Q5184783"}
    start_urls = ["https://www.crewclothing.co.uk/customer-services/stores/"]
    rules = [Rule(LinkExtractor(r"/customer-services/stores/[-\w]+/$"), "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item.get("lat"):
            if m := re.search(r"dblCustomerlatitude\s*=\s*(-?\d+\.\d+);", response.text):
                item["lat"] = m.group(1)
        if not item.get("lon"):
            if m := re.search(r"dblCustomerlongitude\s*=\s*(-?\d+\.\d+);", response.text):
                item["lon"] = m.group(1)

        yield item
