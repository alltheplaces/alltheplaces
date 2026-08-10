import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SixtSpider(SitemapSpider, StructuredDataSpider):
    name = "sixt"
    item_attributes = {"brand": "Sixt", "brand_wikidata": "Q705664"}
    sitemap_urls = ["https://www.sixt.co.uk/sitemap_index.xml"]
    sitemap_rules = [(r"\/car-hire\/[-\w]+\/[-\w]+\/[-\w]+\/$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    sitemap_follow = ["/car-hire/"]
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["country"] = item.pop("state")
        if m := re.match(r"^Car hire (.+)\|? (?:SIXT rent a car|SIXT Car Rental|SIXT)$", item["name"], re.IGNORECASE):
            item["branch"] = m.group(1)
            item["name"] = None

        if (oh := item.get("opening_hours")) is not None:
            # Sixt puts afternoon shifts of split opening hours in specialOpeningHoursSpecification,
            # which the linked data parser (correctly) ignores.
            for rule in ld_data.get("specialOpeningHoursSpecification") or []:
                if isinstance(rule, dict):
                    LinkedDataParser._parse_opening_hours_specification(oh, rule, "%H:%M")
            # Sixt uses 00:00-00:00 for round the clock branches, which is dropped as ambiguous.
            for rule in ld_data.get("openingHoursSpecification") or []:
                if isinstance(rule, dict) and rule.get("opens") == rule.get("closes") == "00:00":
                    for day in rule.get("dayOfWeek") or []:
                        oh.add_range(day, "00:00", "24:00")

        yield item
