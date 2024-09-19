from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class SpeedyServicesGBSpider(CrawlSpider, StructuredDataSpider):
    name = "speedy_services_gb"
    item_attributes = {
        "brand": "Speedy",
        "brand_wikidata": "Q7575722",
    }
    start_urls = ["https://www.speedyservices.com/depot/a-z"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www.speedyservices.com/depot/[\w-]+-\d+"),
            callback="parse",
        ),
    ]
    search_for_twitter = False
    search_for_facebook = False

    def pre_process_data(self, ld_data, **kwargs):
        filtered_times = []
        for spec in LinkedDataParser.get_case_insensitive(ld_data, "OpeningHoursSpecification"):
            if spec.get("Opens") == "00:00" and spec.get("Closes") == "00:00":
                spec["Opens"] = "closed"
                spec["Closes"] = "closed"
            elif spec.get("opens") == "00:00" and spec.get("closes") == "00:00":
                spec["opens"] = "closed"
                spec["closes"] = "closed"
            filtered_times.append(spec)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        yield item
