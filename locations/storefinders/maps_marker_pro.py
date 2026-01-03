from typing import AsyncIterator, Iterable

from scrapy import Selector, Spider
from scrapy.http import FormRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS_BY_FREQUENCY, OpeningHours
from locations.items import Feature


class MapsMarkerProSpider(Spider):
    """
    MapsMarkerPro store finder with official URL of:
    https://www.mapsmarker.com/

    To use this store finder, specify an 'allowed_domains' value for the
    domain containing a store finder page. As this is a WordPress plugin, the
    WordPress API endpoint usually resides at the same path. If for some
    reason a different path is observed, specify a full 'start_urls' value for
    the customised WordPress API endpoint location.

    Also specify a value for 'days' as a language-specific list of days as
    specified in locations/hours.py (such as DAYS_EN). This value for 'days'
    will allow opening hours to be extracted. If 'days' is not specified, an
    attempt will be made to automatically detect the language.

    The following methods can be overridden:
    1. parse_opening_hours
         Override this method to provide customised opening hours extraction
         and parsing, should this be necessary. By default, opening hours are
         extracted by guessing the language these opening hours are provided
         in. Use the 'days' attribute to specify the language explicitly.
    2. parse_item
         Override this method to clean up extracted data such as location
         names with unwanted suffixes.
    """

    allowed_domains: list[str] = []
    start_urls: list[str] = []
    days: dict | None = None

    async def start(self) -> AsyncIterator[FormRequest]:
        formdata = {
            "action": "mmp_map_markers",
            "type": "map",
        }
        if len(self.start_urls) == 0 and len(self.allowed_domains) == 1:
            yield FormRequest(
                url=f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php", method="POST", formdata=formdata
            )
        elif len(self.start_urls) == 1:
            yield FormRequest(url=self.start_urls[0], method="POST", formdata=formdata)
        else:
            raise ValueError(
                "Specify one domain name in the allowed_domains list attribute or one URL in the start_urls list attribute."
            )

    def parse(self, response: TextResponse) -> Iterable[FormRequest]:
        # Response is a GeoJSON object
        ids = []
        for location in response.json()["data"]["features"]:
            ids.append(location["properties"]["id"])

        formdata = {
            "action": "mmp_marker_popups",
            "id": ",".join(ids),
            "lang": "",
        }
        yield FormRequest(
            url=response.url,
            method="POST",
            formdata=formdata,
            callback=self.parse_popups,
            meta={"features": response.json()["data"]["features"]},
        )

    def parse_popups(self, response: TextResponse) -> Iterable[Feature]:
        features = response.meta["features"]
        popups = {popup["id"]: popup for popup in response.json()["data"]}
        for feature in features:
            popup = popups[feature["properties"]["id"]]

            item = DictParser.parse(feature["properties"])
            item["geometry"] = feature["geometry"]

            hours_selector = Selector(text=popup["popup"])
            self.parse_opening_hours(item, feature, popup, hours_selector)

            yield from self.parse_item(item, feature, popup)

    def parse_opening_hours(self, item: Feature, feature: dict, popup: dict, hours_selector: Selector) -> None:
        if hours_string := " ".join(
            filter(
                None,
                map(
                    str.strip,
                    hours_selector.xpath("//div[contains(@class, 'real-opening-hours')]/ul/li/text()").getall(),
                ),
            )
        ):
            item["opening_hours"] = OpeningHours()
            if self.days:
                item["opening_hours"].add_ranges_from_string(hours_string, days=self.days)
            else:
                # Otherwise, iterate over the possibilities until we get a first match
                self.logger.warning(
                    "Attempting to automatically detect the language of opening hours data. Specify spider parameter days = DAYS_EN or the appropriate language code to suppress this warning."
                )
                for days_candidate in DAYS_BY_FREQUENCY:
                    item["opening_hours"].add_ranges_from_string(hours_string, days=days_candidate)
                    if item["opening_hours"].as_opening_hours():
                        break

    def parse_item(self, item: Feature, feature: dict, popup: dict) -> Iterable[Feature]:
        yield item
