from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class StoreRocketSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "storerocket.io"}

    storerocket_id = ""
    base_url = None

    def start_requests(self):
        yield JsonRequest(url=f"https://storerocket.io/api/user/{self.storerocket_id}/locations")

    def parse(self, response, **kwargs):
        if not response.json()["success"]:
            return

        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)

            item["street_address"] = ", ".join(filter(None, [location["address_line_1"], location["address_line_2"]]))

            item["facebook"] = location.get("facebook")
            item["extras"]["instagram"] = location.get("instagram")
            item["twitter"] = location.get("twitter")

            if self.base_url:
                item["website"] = f'{self.base_url}?location={location["slug"]}'

            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_name, day_hours in location["hours"].items():
                hours_string = hours_string + f" {day_name}: {day_hours}"
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item

    def storefinder_exists(response: Response) -> bool | Request:
        # Example: https://barre3.com/studio-locations
        # Only after DOM load
        # <script id="store-rocket-script" src="https://cdn.storerocket.io/widget.js"></script>

        # Example: https://soapynoble.com/
        # <script type="text/javascript" async="" src="https://cdn.storerocket.io/js/widget-mb.js"></script>
        if response.xpath('//script[contains(@src, "https://cdn.storerocket.io/widget")]').get():
            return True

        # Example: https://soapynoble.com/
        # Example: https://ribcrib.com/locations/
        if response.xpath('//div[@id="storerocket-widget"]').get():
            return True

        return False

    def extract_spider_attributes(response: Response) -> dict | Request:
        attribs = {}

        if response.xpath('//div[@id="storerocket-widget"]/@data-storerocket-id').get():
            attribs["storerocket_id"] = response.xpath('//div[@id="storerocket-widget"]/@data-storerocket-id').get()

        # TODO: https://barre3.com/studio-locations and similar inject JavaScript into a Playwright page for this URL to extract the key from object Window.StoreRocket.configs.projectId which in this case is jN49m3n4Gy

        return attribs
