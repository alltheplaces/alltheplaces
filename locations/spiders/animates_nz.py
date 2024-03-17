import json

from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AnimatesNZSpider(Spider):
    name = "animates_nz"
    allowed_domains = [
        "www.animates.co.nz",
    ]
    start_urls = ["https://www.animates.co.nz/store-finder"]
    item_attributes = {"brand": "Animates", "brand_wikidata": "Q110299350"}

    def parse(self, response):
        locations_js = response.xpath(
            '//script[contains(text(), "Aheadworks_StoreLocator/js/view/location-list") and contains(text(), "locationRawItems")]/text()'
        ).get()
        locations = parse_js_object(locations_js)["#aw-storelocator-navigation"]["Magento_Ui/js/core/app"][
            "components"
        ]["locationList"]["locationRawItems"]

        for tab in locations:
            location = tab["tabs"][0]

            item = DictParser.parse(location)
            item["website"] = "https://www.animates.co.nz/store-finder/" + location["slug"]
            item["street_address"] = item.pop("street")
            item["opening_hours"] = OpeningHours()
            for day, hours in json.loads(location["hoursofoperation"])["hoursofoperation"].items():
                item["opening_hours"].add_range(day, hours[0], hours[1])

            item["extras"] = Categories.SHOP_PET.value

            yield item
