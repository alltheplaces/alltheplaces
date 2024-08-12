import json

from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


#
# A spider for the embedded behaviours of
#
# https://aheadworks.com/store-locator-extension-for-magento-1
# https://aheadworks.com/store-locator-extension-for-magento-2
#
# TODO: Autodetection
# TODO: Find more examples of this in the wild
#
class AheadworksSpider(Spider):
    def parse(self, response):
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
            for day, hours in json.loads(location["hoursofoperation"])["hoursofoperation"].items():
                item["opening_hours"].add_range(day, hours[0], hours[1])

            yield from self.post_process_item(item, response, location) or []

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item, response, location):
        """Override with any post-processing on the item."""
        yield item
