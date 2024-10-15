from typing import Any, Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DELIMITERS_EN, NAMED_DAY_RANGES_EN, NAMED_TIMES_EN, OpeningHours
from locations.items import Feature
from locations.spiders.papa_johns import PAPA_JOHNS_SHARED_ATTRIBUTES

"""
A common storefinder for Papa Johns in a number of countries.

To use this storefinder simply specify the storefinder url in start_urls and also a list of language codes
for which there is available data, with the primary language listed first.

If en is not available or suitable for 'hours_text" then override hours_language, days, named_times, named_day_ranges and delimiters as required
"""


class PapaJohnsStorefinderSpider(Spider):
    item_attributes = PAPA_JOHNS_SHARED_ATTRIBUTES
    languages = []
    hours_language = "en"
    days = DAYS_EN
    delimiters = DELIMITERS_EN
    named_times = NAMED_TIMES_EN
    named_day_ranges = NAMED_DAY_RANGES_EN

    def start_requests(self) -> Iterable[Request]:
        url = urlparse(self.start_urls[0])
        yield JsonRequest(
            url=url._replace(path="/api/outlet/list/", query="all=true").geturl(),
            headers={"Referer": self.start_urls[0]},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("list", []):
            if location["public"] is False:
                continue

            item = DictParser.parse(location)

            item["name"] = None

            item["addr_full"] = location.get("address", {}).get(self.languages[0])

            for lang in self.languages:
                item["extras"][f"addr:full:{lang}"] = location.get("address", {}).get(lang)

            item["branch"] = (
                location.get("name", {}).get(self.languages[0]).replace("Papa John's ", "").replace("Papa Johns ", "")
            )
            for lang in self.languages:
                item["extras"][f"branch:{lang}"] = (
                    location.get("name", {}).get(lang).replace("Papa John's ", "").replace("Papa Johns ", "")
                )

            item["phone"] = location.get("phone", [{}])[0].get("value")

            item["lat"], item["lon"] = location["points"]

            storefinder_url = urlparse(self.start_urls[0])
            path = storefinder_url.path.strip("/").split("/")[0] + "/" + str(item["ref"]) + "/"
            item["website"] = storefinder_url._replace(path=path, query=None).geturl()

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                location.get("hours_text", {}).get(self.hours_language),
                self.days,
                self.named_day_ranges,
                self.named_times,
                self.delimiters,
            )
            if (
                item["opening_hours"].as_opening_hours == ""
                and location.get("hours_text", {}).get(self.hours_language) is not None
            ):
                self.logger.warning(f"Error parsing hours: {location.get('hours_text', {}).get(self.hours_language)}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")

            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        """Override with any post processing on the item"""
        yield item
