import json
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.selector.unified import Selector

from locations.hours import DAYS_DE, DELIMITERS_DE, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CallAPizzaDESpider(StructuredDataSpider):
    name = "call_a_pizza_de"
    item_attributes = {"brand": "Call a Pizza", "brand_wikidata": "Q1027107"}
    start_urls = ["https://www.call-a-pizza.de/bestellen"]
    store_ids = dict()  # Mapping from ref (URL) to internal store ID
    store_data = dict()  # Store ID to lon/lat
    opening_hours = dict()  # ref (URL) to parsed opening hours
    RE_OPENING_DAYS = re.compile(OpeningHours.any_day_extraction_regex(days=DAYS_DE, delimiters=DELIMITERS_DE))
    RE_DELIMITERS = re.compile(OpeningHours.delimiters_regex(delimiters=DELIMITERS_DE))
    RE_HOURS = re.compile(r"(\d\d:\d\d) - (\d\d:\d\d)")

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        # Coordinates are stored separately in a JavaScript call.
        store_data_json = response.xpath('//script[contains(., "store_data_map")]').re_first(
            r"JSON.parse\('(\[.*?\])'\);"
        )
        store_list = json.loads(store_data_json)
        self.store_data = {s["store_id"]: s for s in store_list}

        # Parse and store opening hours. The microdata parser can't extract them.
        self.opening_hours = dict()
        for store in response.xpath('//tr[contains(@class, "bestellen_store")]'):
            ref = store.xpath('descendant::span[@itemprop="url"]/text()').get()
            store_id = store.attrib["data-id"]
            self.store_ids[ref] = store_id
            self.opening_hours[ref] = self.extract_opening_hours(store)

        yield from self.parse_sd(response)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # Merge item from StructuredDataSpider with lon/lat and opening hours parsed separately
        item["ref"] = ld_data["url"]
        if item["name"].startswith("Call a Pizza "):
            item["branch"] = item["name"].removeprefix("Call a Pizza ")
            item["name"] = "Call a Pizza"
        store_id = self.store_ids[item["ref"]]
        item["lon"] = self.store_data[store_id]["longitude"]
        item["lat"] = self.store_data[store_id]["latitude"]
        item["opening_hours"] = self.opening_hours[item["ref"]]
        yield item

    def extract_opening_hours(self, store: Selector) -> OpeningHours:
        opening = OpeningHours()
        for days_line in store.xpath('descendant::div[@class="bestellen_oph_left"]'):
            opening_days = "".join(days_line.xpath("(b|.)/text()").getall())
            if self.RE_OPENING_DAYS.match(opening_days):
                hours_line = (
                    days_line.xpath('following-sibling::div[@class="bestellen_oph_right"]/text()').get().strip()
                )
                match = self.RE_HOURS.match(hours_line)
                if match:
                    day_interval = opening.days_in_day_range(self.RE_DELIMITERS.split(opening_days), days=DAYS_DE)
                    opening.add_days_range(day_interval, match.group(1), match.group(2))
        return opening
