import json

from scrapy import Spider

from locations.items import Feature


class PepcoSpider(Spider):
    name = "pepco"
    item_attributes = {"brand": "Pepco", "brand_wikidata": "Q11815580"}
    start_urls = ["https://pepco.eu/find-store/"]

    def parse(self, response, **kwargs):
        for location in json.loads(response.xpath("//@shops-map-markers").get()):
            yield Feature(
                ref=location["shop_id"],
                lat=location["coordinates"]["lat"],
                lon=location["coordinates"]["lng"],
                name=response.xpath(
                    '//div[@shops-map-marker-anchor="{}"]//@data-shop-name'.format(location["shop_id"])
                ).get(),
                addr_full=response.xpath(
                    '//div[@shops-map-marker-anchor="{}"]//@data-shop-address'.format(location["shop_id"])
                ).get(),
            )
