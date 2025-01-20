import re
from typing import Any
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


# Sitemap is there, but it doesn't provide all locations
class CaptainDSpider(CrawlSpider, StructuredDataSpider):
    name = "captain_d"
    item_attributes = {"brand": "Captain D's", "brand_wikidata": "Q5036616"}
    start_urls = ["https://locations.captainds.com/site-map/US/"]
    rules = [
        Rule(LinkExtractor(allow=r"/site-map/us/\w{2}/$")),
        Rule(LinkExtractor(allow=r"/site-map/us/\w{2}/[-\w]+/$"), callback="parse_locations"),
    ]
    json_parser = "chompjs"

    # Ultimate POI page urls are not directly available to the CrawlSpider
    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for slug in re.findall(r"\"localpage_url_id\"[:\s]+\"(.+?)\"", response.text):
            yield Request(url=urljoin(response.url.replace("site-map", "ll"), f"{slug}/"), callback=self.parse_sd)

    def pre_process_data(self, ld_data: dict, **kwargs):
        if hours := ld_data.get("openingHoursSpecification"):
            # Monday closing time is missing, assuming same as Tuesday's closing time, based on Google Maps data
            monday_index, tuesday_index = None, None
            for index, rule in enumerate(hours):
                if rule.get("dayOfWeek") == ["Monday"]:
                    monday_index = index
                if rule.get("dayOfWeek") == ["Tuesday"]:
                    tuesday_index = index
            if monday_index is not None and tuesday_index is not None:
                if hours[monday_index]["opens"] == hours[tuesday_index]["opens"] and not hours[monday_index]["closes"]:
                    ld_data["openingHoursSpecification"][monday_index]["closes"] = ld_data["openingHoursSpecification"][
                        tuesday_index
                    ]["closes"]
