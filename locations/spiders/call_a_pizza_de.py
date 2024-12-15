import json
import re

from scrapy.spiders import Spider

from locations.hours import OpeningHours, DAYS_DE, DELIMITERS_DE
from locations.items import Feature


class CallAPizzaDESpider(Spider):
    name = "call_a_pizza_de"
    item_attributes = {"brand": "Call a Pizza", "brand_wikidata": "Q1027107"}
    start_urls = ["https://www.call-a-pizza.de/bestellen"]
    RE_OPENING_DAYS = re.compile(OpeningHours.any_day_extraction_regex(days=DAYS_DE, delimiters=DELIMITERS_DE))
    RE_DELIMITERS = re.compile(OpeningHours.delimiters_regex(delimiters=DELIMITERS_DE))
    RE_HOURS = re.compile(r"(\d\d:\d\d) - (\d\d:\d\d)")

    def parse(self, response, **kwargs):
        # Coordinates are stored separately in a JavaScript call.
        store_data_json = response.xpath('//script[contains(., "store_data_map")]').re_first(
            r"JSON.parse\('(\[.*?\])'\);"
        )
        store_data = json.loads(store_data_json)
        store_data = {s["store_id"]: s for s in store_data}
        for store in response.xpath('//tr[@class="bestellen_store"]'):
            ref = store.attrib["data-id"]
            properties = {
                "ref": ref,
            }
            fields = {
                "name": "name",
                "street_address": "streetAddress",
                "postcode": "postalCode",
                "city": "addressLocality",
                "phone": "telephone",
            }
            for atp_key, site_key in fields.items():
                properties[atp_key] = store.xpath(f'descendant::span[@itemprop="{site_key}"]/text()').get().strip()
            if properties["name"].startswith("Call a Pizza "):
                properties["branch"] = properties["name"].removeprefix("Call a Pizza ")
                properties["name"] = "Call a Pizza"
            properties["website"] = response.urljoin(store.xpath('descendant::a[@class="storelink"]/@href').get())
            properties["lon"] = store_data[ref]["longitude"]
            properties["lat"] = store_data[ref]["latitude"]
            properties["opening_hours"] = self.extract_opening_hours(store)
            # Empty opening hours -> closed on all days
            if properties["opening_hours"]:
                yield Feature(properties)

    def extract_opening_hours(self, store):
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