from scrapy import Spider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenDKSpider(Spider):
    name = "seven_eleven_dk"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = ["https://7eleven-prod.azurewebsites.net/api/stores/all"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = location.pop("address")

            item = DictParser.parse(location)

            item["ref"] = location["storeNumber"]

            if location["type"] == "shell":
                apply_category(Categories.FUEL_STATION, item)
                apply_yes_no("car_wash", item, location["hasCarwash"])
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
