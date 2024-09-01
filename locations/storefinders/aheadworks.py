from json import loads
from typing import Iterable

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionResponseRule
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class AheadworksSpider(Spider, AutomaticSpiderGenerator):
    """
    Documentation available at:
    1. https://aheadworks.com/store-locator-extension-for-magento-1
    2. https://aheadworks.com/store-locator-extension-for-magento-2

    To use this spider, supply a 'start_url' for the store finder page that
    contains embedded JavaScript with a complete store list. The 'post_process_item'
    method can be overridden if changes to extracted data is necessary, for
    example, to clean up location names.
    """

    detection_rules = [
        DetectionResponseRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+).*)$",
            xpaths={"__": r'//div[@id="aw-storelocator-navigation"]/@id'},
        )
    ]

    def parse(self, response: Response) -> Iterable[Feature]:
        features_js = response.xpath(
            '//script[contains(text(), "Aheadworks_StoreLocator/js/view/location-list") and contains(text(), "locationRawItems")]/text()'
        ).get()
        features = parse_js_object(features_js)["#aw-storelocator-navigation"]["Magento_Ui/js/core/app"]["components"][
            "locationList"
        ]["locationRawItems"]

        for tab in features:
            feature = tab["tabs"][0]
            self.pre_process_data(feature)

            if feature.get("coming_soon") == "1":
                continue

            item = DictParser.parse(feature)
            item["website"] = self.start_urls[0] + feature["slug"]
            item["street_address"] = item.pop("street")

            item["opening_hours"] = OpeningHours()
            if hours_dict := loads(feature["hoursofoperation"])["hoursofoperation"]:
                for day, hours in hours_dict.items():
                    item["opening_hours"].add_range(day, hours[0], hours[1])

            yield from self.post_process_item(item, response, feature) or []

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
