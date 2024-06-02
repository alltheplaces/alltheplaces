from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import FormRequest, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import DAYS_BY_FREQUENCY, OpeningHours
from locations.items import Feature

# MapsMarkerPro store finder with official URL of
# https://www.mapsmarker.com/
#
# To use this store finder, specify an 'allowed_domains' value for the domain
# containing a store finder page. As this is a WordPress plugin, the WordPress
# API endpoint usually resides at the same path. If for some reason a
# different path is observed, specify a full 'start_urls' value for the
# customised WordPress API endpoint location.
#
# Also specify a value for 'days' as a language-specific list of days as
# specified in locations/hours.py (such as DAYS_EN). This value for 'days'
# will allow opening hours to be extracted. If 'days' is not specified, an
# attempt will be made to automatically detect the language.
#
# The following methods can be overridden:
# 1. parse_opening_hours
#      Override this method to provide customised opening hours extraction and
#      parsing, should this be necessary. By default, opening hours are
#      extracted by guessing the language these opening hours are provided in.
#      Use the 'days' attribute to specify the language explicitly.
# 2. parse_item
#      Override this method to clean up extracted data such as location names
#      with unwanted suffixes.


class MapsMarkerProSpider(Spider, AutomaticSpiderGenerator):
    days: dict = None
    detection_rules = [
        DetectionRequestRule(
            url=r"^https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)\/wp-admin\/admin-ajax\.php$",
            js_objects={"__": 'if (typeof window.MapsMarkerPro == "function") {true} else {null}'},
        ),
        DetectionRequestRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+)(?:\/[^\/]+)+\/wp-admin\/admin-ajax\.php)$",
            js_objects={"__": 'if (typeof window.MapsMarkerPro == "function") {true} else {null}'},
        ),
    ]

    def start_requests(self):
        formdata = {
            "action": "mmp_map_markers",
            "type": "map",
        }
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                url = f"https://{domain}/wp-admin/admin-ajax.php"
                yield FormRequest(url=url, method="POST", formdata=formdata, callback=self.parse)
        elif len(self.start_urls) != 0:
            for url in self.start_urls:
                yield FormRequest(url=url, method="POST", formdata=formdata, callback=self.parse)

    def parse(self, response: Response):
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

    def parse_popups(self, response: Response):
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
