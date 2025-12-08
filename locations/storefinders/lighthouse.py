import re
from hashlib import sha1
from html import unescape
from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_BY_FREQUENCY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

# Lighthouse e-commerce platform store finder, with official URL of
# https://www.lighthouse.gr/
#
# This store finder is detected via a HTML node:
#   <meta name="generator" content="Created by Lighthouse, powered by VENDD
#   e-commerce platform - www.lighthouse.gr" />
# As well as HTML nodes for each location/feature:
#   <article data-control="box" data-latitude=".." data-longitude="..">
#
# To use this spider, specify a 'start_url' for the store finder page. If
# opening hours are provided, also specify 'days' as a language-specific list
# of days as specified in locations/hours.py (such as DAYS_GR). If 'days' is
# not specified, an attempt will be made to automatically detect the language.
#
# The following methods can be overridden:
# 1. parse_extras
#      Override this method to provide customised feature tag extraction of
#      facts such as whether the feature has a publicly accessible toilet. By
#      default, known feature tags are automatically extracted.
# 2. parse_opening_hours
#      Override this method to provide customised opening hours extraction
#      and parsing, should this be necessary. By default, opening hours are
#      extracted by guessing the language these opening hours are provided in.
#      Use the 'days' attribute to specify the language explicitly.
# 3. parse_item
#      Override this method to clean up extracted data such as location names
#      with unwanted suffixes.


class LighthouseSpider(Spider):
    days: dict = None

    def parse(self, response: Response):
        for location in response.xpath('//article[@data-control="box"]'):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["name"] = (
                location.xpath('.//*[contains(@class, "name") and not(contains(@class, "name-"))]/text()')
                .get("")
                .strip()
            )
            item["addr_full"] = clean_address(
                location.xpath('(.//*[contains(@class, "address-one")])[1]//text()').getall()
            )

            item["phone"] = location.xpath('.//a[contains(@href, "tel:")]/@href').get("").replace("tel:", "")
            if not item["phone"]:
                item["phone"] = (
                    location.xpath(
                        '(.//*[contains(@class, "phone") and not(contains(@class, "icon-open-hours"))])[1]/text()'
                    )
                    .get("")
                    .split(",")[0]
                    .strip()
                )
            item["email"] = location.xpath('.//a[contains(@href, "mailto:")]/@href').get("").replace("mailto:", "")
            if not item["email"]:
                item["email"] = (
                    location.xpath('.//*[contains(@class, "email") and not(@data-cfemail)]/text()')
                    .get("")
                    .split(",")[0]
                    .strip()
                )

            # If no unique identifier is available, generate one from
            # coordinates instead.
            if item["ref"] is None:
                coordinates = ",".join([item["lat"], item["lon"]])
                item["ref"] = sha1(coordinates.encode("UTF-8")).hexdigest()

            self.parse_extras(item, location)
            self.parse_opening_hours(item, location)

            yield from self.parse_item(item, location) or []

    def parse_extras(self, item: Feature, location: Selector) -> None:
        extra_features = location.xpath('.//div[contains(@class, "extra-features-container")]/ul/li/@class').getall()
        apply_yes_no(Extras.CAR_WASH, item, "car_wash" in extra_features or "carwash" in extra_features, True)
        apply_yes_no(Extras.TOILETS, item, "toilet" in extra_features or "wc" in extra_features, True)
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "disabled-wc" in extra_features, True)
        apply_yes_no(Extras.ATM, item, "atm" in extra_features, True)
        apply_yes_no(Extras.WIFI, item, "wifi" in extra_features, True)
        apply_yes_no(Extras.COMPRESSED_AIR, item, "aircompresor" in extra_features, True)

    def parse_opening_hours(self, item: Feature, location: Selector) -> None:
        if hours_string := " ".join(
            filter(None, map(str.strip, location.xpath('.//*[contains(@class, "icon-open-hours")]//text()').getall()))
        ):
            hours_string = re.sub(r"\s+", " ", unescape(hours_string))
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

    def parse_item(self, item: Feature, location: Selector) -> Iterable[Feature]:
        yield item
