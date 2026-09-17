import json
from typing import Any, Iterable
from urllib.parse import unquote

from scrapy.http import Request, Response
from twisted.python.failure import Failure

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.libcal import PHONE_OR_REGEX, LibCalSpider


class OcPublicLibrariesUSSpider(LibCalSpider):
    name = "oc_public_libraries_us"
    item_attributes = {"operator": "OC Public Libraries", "operator_wikidata": "Q66369360"}
    libcal_host = "ocpl.libcal.com"
    libcal_iid = 6287
    country = "US"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature | Request]:
        if item["branch"] == "Administrative Headquarters":
            # Administration building, not a library branch.
            return
        if item["branch"] in ("La Habra", "Garden Grove Main"):
            # Closed for renovation since May 2025 (~24 months, per
            # libraries.oc.gov/LH-updates and /GGM-updates); branch pages are
            # unpublished so no location is available.
            return
        item["name"] = "{} Library".format(item["branch"])
        # LibCal has no coordinates and rarely an address, so they are taken
        # from the branch page on the library website.
        yield Request(
            item["website"],
            callback=self.parse_branch_page,
            errback=self.parse_branch_page_error,
            cb_kwargs={"item": item},
        )

    def parse_branch_page(self, response: Response, item: Feature) -> Iterable[Feature]:
        # ocpl.org redirects to libraries.oc.gov.
        item["website"] = response.url
        # e.g. "Seal Beach - Mary Wilson Library | OC Public Libraries"
        if title := response.xpath('//meta[@property="og:title"]/@content').get():
            item["name"] = title.split(" | ", 1)[0].strip()
            item["branch"] = item["name"].removesuffix(" Library")
        item["image"] = response.xpath('//meta[@property="og:image"]/@content').get()

        # The email addresses in LibCal are outdated (@occr.ocgov.com rather
        # than @occr.oc.gov), so the branch page's contact details are
        # preferred.
        if email := response.xpath('//div[@class="info-email"]//a[starts-with(@href, "mailto:")]/@href').get():
            item["email"] = unquote(email.removeprefix("mailto:")).split("?", 1)[0]
        if phones := [
            number
            for href in response.xpath('//div[@class="info-phone"]//a[starts-with(@href, "tel:")]/@href').getall()
            for number in PHONE_OR_REGEX.split(unquote(href))
            if number
        ]:
            item["phone"] = "; ".join(phones)

        address = response.xpath('//p[@class="address"]')
        item["street_address"] = merge_address_lines(
            address.xpath('./span[@class="address-line1" or @class="address-line2"]/text()').getall()
        )
        item["city"] = address.xpath('./span[@class="locality"]/text()').get()
        item["state"] = address.xpath('./span[@class="administrative-area"]/text()').get()
        item["postcode"] = address.xpath('./span[@class="postal-code"]/text()').get()

        # The branch map is a Drupal geofield map with a GeoJSON point.
        if script := response.xpath('//script[@data-drupal-selector="drupal-settings-json"]/text()').get():
            for geofield_map in (json.loads(script).get("geofield_google_map") or {}).values():
                for feature in (geofield_map.get("data") or {}).get("features") or []:
                    if (feature.get("geometry") or {}).get("type") == "Point":
                        item["lon"], item["lat"] = feature["geometry"]["coordinates"]
                        break

        yield item

    def parse_branch_page_error(self, failure: Failure) -> Iterable[Any]:
        # Keep the location, without address and coordinates, rather than
        # silently dropping it.
        request = failure.request  # ty: ignore[unresolved-attribute]
        self.logger.warning("Failed to fetch branch page %s: %r", request.url, failure.value)
        self.crawler.stats.inc_value(f"atp/{self.name}/branch_page_failed")
        yield request.cb_kwargs["item"]
