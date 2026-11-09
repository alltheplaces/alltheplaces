import json
import re

from scrapy.http import TextResponse

from locations.structured_data_spider import StructuredDataSpider


class AvisSpider(StructuredDataSpider):
    name = "avis"

    item_attributes = {
        "brand": "Avis",
        "brand_wikidata": "Q791136",
    }

    start_urls = [
        "https://www.avis.com/en/locations/avisworldwide",
    ]

    LOCATION_DATA_RE = re.compile(r'"locationData":({.+?}),"i18n":{"locationIndex')

    def extract_location_data(self, response: TextResponse) -> dict:
        """Extract locationData JSON from page."""

        if not (script := response.xpath('//*[contains(text(), "locationData")]/text()').get()):
            return {}

        if not (match := self.LOCATION_DATA_RE.search(script.replace("\\", ""))):
            return {}

        return json.loads(match.group(1))

    def follow_location_links(
        self,
        response: TextResponse,
        callback,
    ):
        """Follow all child location links."""

        location_data = self.extract_location_data(response)

        for node in location_data.values():
            for child in node.get("children", {}).values():
                if link := child.get("link"):
                    yield response.follow(
                        link,
                        callback=callback,
                    )

    def parse(self, response: TextResponse, **kwargs):
        yield from self.follow_location_links(
            response,
            self.parse_location,
        )

    def parse_location(self, response: TextResponse, **kwargs):
        yield from self.follow_location_links(
            response,
            self.parse_details,
        )

    def parse_details(self, response: TextResponse, **kwargs):
        yield from response.follow_all(
            response.xpath('//*[@data-testid="location-map-view-station-description"]/@href').getall(),
            callback=self.parse_sd,
        )
