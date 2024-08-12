from json import loads

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionResponseRule
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# Documentation available at:
# 1. https://aheadworks.com/store-locator-extension-for-magento-1
# 2. https://aheadworks.com/store-locator-extension-for-magento-2
#
# To use this spider, supply a 'start_url' for the store finder page that
# contains embedded JavaScript with a complete store list. The 'parse_item'
# method can be overridden if changes to extracted data is necessary, for
# example, to clean up location names.


class AheadworksSpider(Spider, AutomaticSpiderGenerator):
    detection_rules = [
        DetectionResponseRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+).*)$",
            xpaths={"__": r'//div[@id="aw-storelocator-navigation"]/@id'},
        )
    ]

    def parse(self, response: Response):
        locations_js = response.xpath(
            '//script[contains(text(), "Aheadworks_StoreLocator/js/view/location-list") and contains(text(), "locationRawItems")]/text()'
        ).get()
        locations = parse_js_object(locations_js)["#aw-storelocator-navigation"]["Magento_Ui/js/core/app"][
            "components"
        ]["locationList"]["locationRawItems"]

        for tab in locations:
            location = tab["tabs"][0]
            self.pre_process_data(location)

            item = DictParser.parse(location)
            item["website"] = self.start_urls[0] + location["slug"]
            item["street_address"] = item.pop("street")
            item["opening_hours"] = OpeningHours()
            for day, hours in loads(location["hoursofoperation"])["hoursofoperation"].items():
                item["opening_hours"].add_range(day, hours[0], hours[1])

            yield from self.post_process_item(item, response, location) or []

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item, response, location):
        """Override with any post-processing on the item."""
        yield item
