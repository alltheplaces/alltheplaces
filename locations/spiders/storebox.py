import json

from scrapy import Spider

from locations.dict_parser import DictParser


class StoreboxSpider(Spider):
    name = "storebox"
    item_attributes = {"brand": "Storebox", "brand_wikidata": "Q117430004"}
    start_urls = ["https://www.yourstorebox.com/en/locations"]

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        for location in DictParser.get_nested_key(data, "allLocations")["results"]:
            if location["status"] != "ACTIVE":
                continue

            item = DictParser.parse(location)

            item["ref"] = location["code"]
            item["addr_full"] = location["address"]["formattedAddressString"]
            item["image"] = location["thumbnail"]["link"]
            item["website"] = f'https://www.yourstorebox.com/en/location-details/{location["linkName"]}'

            yield item
