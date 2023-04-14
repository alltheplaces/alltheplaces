from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class ChargeYourCarGBSpider(Spider):
    name = "charge_your_car_gb"
    item_attributes = {"brand": "Charge Your Car", "brand_wikidata": "Q117706187"}
    start_urls = ["https://m.chargeyourcar.org.uk/api/clusters"]

    def parse(self, response, **kwargs):
        for location in response.json():
            yield JsonRequest(
                url=f'https://m.chargeyourcar.org.uk/api/cluster/{location["id"]}/chargepointpins',
                callback=self.parse_cluster,
            )

    def parse_cluster(self, response, **kwargs):
        for location in response.json()["chargePointPins"]:
            item = DictParser.parse(location)
            item["name"] = location["siteName"]
            item["website"] = f'https://m.chargeyourcar.org.uk/chargePoint?bayNo={location["bayNo"]}'

            # TODO: parse connector data location["connectorStatus"]

            yield item
