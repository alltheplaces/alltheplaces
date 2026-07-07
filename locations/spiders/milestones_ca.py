from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MilestonesCASpider(CrawlSpider, StructuredDataSpider):
    name = "milestones_ca"
    item_attributes = {"brand": "Milestones", "brand_wikidata": "Q6851623"}
    allowed_domains = ["milestonesrestaurants.com"]
    start_urls = ["https://milestonesrestaurants.com/all-locations/"]
    rules = [Rule(LinkExtractor(allow=r"/locations/[^/]+/$"), callback="parse_sd")]
    wanted_types = ["Restaurant"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        oh = OpeningHours()
        for rule in ld_data.get("openingHoursSpecification", []):
            for day in (rule.get("dayOfWeek") or "").split(","):
                oh.add_range(
                    day=day.strip(),
                    open_time=rule.get("opens"),
                    close_time=rule.get("closes"),
                )
        item["opening_hours"] = oh
        apply_category(Categories.RESTAURANT, item)

        yield item
