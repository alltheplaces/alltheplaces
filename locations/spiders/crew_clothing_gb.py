import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class CrewClothingGBSpider(CrawlSpider, StructuredDataSpider):
    name = "crew_clothing_gb"
    item_attributes = {"brand": "Crew Clothing Company", "brand_wikidata": "Q5184783"}
    start_urls = ["https://www.crewclothing.co.uk/customer-services/stores/"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//div[@id="storelistall"]/div/a'), "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if " - Now Closed" in item["name"]:
            item["name"] = item["name"].split(" - ")[0]
            set_closed(item)

        if not item.get("lat"):
            if m := re.search(r"dblCustomerlatitude\s*=\s*(-?\d+\.\d+);", response.text):
                item["lat"] = m.group(1)

        if not item.get("lon"):
            if m := re.search(r"dblCustomerlongitude\s*=\s*(-?\d+\.\d+);", response.text):
                item["lon"] = m.group(1)

        yield item
