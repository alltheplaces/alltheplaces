import json

from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class NorthernRailwayGBSpider(PlaywrightSpider):
    name = "northern_railway_gb"
    item_attributes = {"operator": "Northern", "operator_wikidata": "Q85789775"}
    start_urls = ["https://www.northernrailway.co.uk/api/northern_station_list_auto_complete"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    requires_proxy = True

    def parse(self, response, **kwargs):
        for location in json.loads(response.xpath("//pre/text()").get())["results"]:
            yield JsonRequest(
                "https://www.northernrailway.co.uk/api/stations/data/{}".format(location["crs_code"]),
                callback=self.parse_station,
            )

    def parse_station(self, response, **kwargs):
        location = json.loads(response.xpath("//pre/text()").get())
        item = Feature()
        item["ref"] = item["extras"]["ref:crs"] = location["crs"]
        item["name"] = location["name"]
        item["website"] = "https://www.northernrailway.co.uk/stations/{}".format(location["slug"])

        item["lat"], item["lon"] = url_to_coords(location["google_maps_url"])

        apply_category(Categories.TRAIN_STATION, item)

        yield item
