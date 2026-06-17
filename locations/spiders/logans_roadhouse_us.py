from scrapy import FormRequest, Spider

from locations.dict_parser import DictParser


class LogansRoadhouseUSSpider(Spider):
    name = "logans_roadhouse_us"
    item_attributes = {"brand": "Logan's Roadhouse", "brand_wikidata": "Q6666872"}

    async def start(self):
        yield FormRequest(
            url="https://logansroadhouse.com/wp-admin/admin-ajax.php",
            method="POST",
            formdata={
                "action": "action_slug_api",
                "data[bbox][]": ["-180", "-90", "180", "90"],
                "data[center][]": ["0", "0"],
                "data[area]": "true",
                "url": "locations",
            },
            callback=self.parse,
        )

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["lat"] = location["location_latitude"]
            item["lon"] = location["location_longitude"]
            item["website"] = item["ref"] = location["store_buttons_local_link"]
            item["street_address"] = location["address"]
            item["city"] = location["address_state"].split(", ")[0]
            item["postcode"] = location["address_state"].split(", ")[2]
            item.pop("name")

            yield item
