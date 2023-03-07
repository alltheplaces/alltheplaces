import collections
import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SpecsaversCASpider(CrawlSpider):
    name = "specsavers_ca"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    start_urls = ["https://www.specsavers.ca/stores/full-store-list"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.specsavers\.ca\/stores\/(?!full-store-list)((?!<\/).+)$"),
            callback="parse_store",
        )
    ]

    def parse_store(self, response):
        data_raw = response.xpath(
            '//script[@type="application/json" and @data-drupal-selector="drupal-settings-json"]/text()'
        ).get()
        data_json = json.loads(data_raw)
        for guid in data_json:
            if not isinstance(data_json[guid], collections.abc.Mapping):
                continue
            if data_json[guid].get("type") != "view_store":
                continue
            location = data_json[guid]["store"]
            item = DictParser.parse(location)
            address_lines = []
            if isinstance(location["address"]["second_line"], str):
                address_lines.append(location["address"]["second_line"].strip())
            if isinstance(location["address"]["first_line"], str):
                address_lines.append(location["address"]["first_line"].strip())
            item["street_address"] = ", ".join(address_lines)
            item["website"] = response.url
            oh = OpeningHours()
            for day in location["opening_times"]:
                open_time = "".join(day["open"].upper().split())
                if ":" not in open_time:
                    open_time = open_time.replace("AM", ":00AM").replace("PM", ":00PM")
                close_time = "".join(day["close"].upper().split())
                if ":" not in close_time:
                    close_time = close_time.replace("AM", ":00AM").replace("PM", ":00PM")
                oh.add_range(day["day"], open_time, close_time, "%I:%M%p")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
