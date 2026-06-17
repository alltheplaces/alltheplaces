import json
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class OldNationalBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "old_national_bank_us"
    item_attributes = {"brand": "Old National Bank", "brand_wikidata": "Q17520701"}
    sitemap_urls = ["https://locations.oldnational.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations\.oldnational\.com/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]

    @staticmethod
    def parse_hours_from_json(hours_json: str) -> OpeningHours:
        """
        Parse opening hours from JSON data containing day and interval information.

        :param hours_json: JSON string with format: [{"day": "MONDAY", "intervals": [{"start": 0, "end": 2359}], "isClosed": false}, ...]
        :returns: OpeningHours object with parsed hours
        """
        data = json.loads(hours_json)
        oh = OpeningHours()

        for day_data in data:
            day = day_data["day"]
            if day_data.get("isClosed", False):
                oh.set_closed(day)
            else:
                for interval in day_data.get("intervals", []):
                    start_time = f"{interval['start']:04d}"  # Format as HHMM (e.g., "0900")
                    end_time = f"{interval['end']:04d}"
                    oh.add_range(day, start_time, end_time, time_format="%H%M")

        return oh

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Old National Bank ")
        item["image"] = None

        # Check for ATM availability
        if response.xpath('//div[@class="Teaser-service" and contains(text(), "ATM")]'):
            apply_yes_no(Extras.ATM, item, True)

            # Get ATM hours JSON data
            hours_json = response.xpath(
                '//h2[@class="Core-heading" and contains(text(), "ATM")]/..//span[@class="c-hours-today js-hours-today"]/@data-days'
            ).get()

            if hours_json:
                try:
                    atm_oh = self.parse_hours_from_json(hours_json)
                    item["extras"]["opening_hours:atm"] = atm_oh.as_opening_hours()
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    pass

        apply_yes_no(
            Extras.DRIVE_THROUGH, item, response.xpath('//div[@class="Teaser-service" and contains(text(), "Drive")]')
        )

        apply_category(Categories.BANK, item)

        yield item
