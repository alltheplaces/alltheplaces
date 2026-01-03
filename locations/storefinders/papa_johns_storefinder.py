from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DELIMITERS_EN, NAMED_DAY_RANGES_EN, NAMED_TIMES_EN, OpeningHours
from locations.items import Feature
from locations.spiders.papa_johns import PAPA_JOHNS_SHARED_ATTRIBUTES


class PapaJohnsStorefinderSpider(Spider):
    """
    A common storefinder for Papa Johns in a number of countries.

    To use this storefinder specify one storefinder url in `start_urls`. Also
    specify a list of language codes for which there is available data within
    the `languages` list attribute, placing the primary language code first in
    the list.

    If langauge code "en" is not available or suitable (observe the
    "hours_text" field in raw API data returned) then override the following
    attributes:
    - `hours_language`: alternative language code other than "en"
    - `days`: DAYS_xx dictionary defined in locations/hours.py
    - `named_times`: NAMED_TIMES_xx dictionary defined in locations/hours.py
    - `named_day_ranges`: NAMED_DAY_RANGES_xx dictionary defined in
                          locations/hours.py
    - `delimiters`: DELIMITERS_xx list defined in locations/hours.py
    """

    item_attributes: dict = PAPA_JOHNS_SHARED_ATTRIBUTES
    start_urls: list[str] = []
    languages: list[str] = []
    hours_language: str = "en"
    days: dict = DAYS_EN
    delimiters: list[str] = DELIMITERS_EN
    named_times: dict = NAMED_TIMES_EN
    named_day_ranges: dict = NAMED_DAY_RANGES_EN

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) != 1:
            raise ValueError("Specify one URL in the start_urls list attribute.")
            return
        url = urlparse(self.start_urls[0])
        yield JsonRequest(
            url=url._replace(path="/api/outlet/list/", query="all=true").geturl(),
            headers={"Referer": self.start_urls[0]},
        )

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json().get("list", []):
            if location["public"] is False:
                continue

            item = DictParser.parse(location)

            item["name"] = None

            item["addr_full"] = location.get("address", {}).get(self.languages[0])
            if len(self.languages) > 1:
                for lang in self.languages:
                    item["extras"][f"addr:full:{lang}"] = location.get("address", {}).get(lang)

            item["branch"] = (
                location.get("name", {})
                .get(self.languages[0], "")
                .replace("Papa John's ", "")
                .replace("Papa Johns ", "")
            )
            if len(self.languages) > 1:
                for lang in self.languages:
                    item["extras"][f"branch:{lang}"] = (
                        location.get("name", {}).get(lang, "").replace("Papa John's ", "").replace("Papa Johns ", "")
                    )

            item["phone"] = location.get("phone", [{}])[0].get("value")

            item["lat"], item["lon"] = location["points"]

            storefinder_url = urlparse(self.start_urls[0])
            path = storefinder_url.path.strip("/").split("/")[0] + "/" + str(item["ref"]) + "/"
            item["website"] = storefinder_url._replace(path=path, query="").geturl()

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
                if self.crawler.stats:
                    self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")

            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        """Override with any post processing on the item"""
        yield item
