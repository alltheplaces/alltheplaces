import html

from scrapy import Spider

from locations.dict_parser import DictParser


class LewiatanPLSpider(Spider):
    name = "lewiatan_pl"
    item_attributes = {"brand": "Lewiatan", "brand_wikidata": "Q11755396"}
    start_urls = ["https://www.lewiatan.pl/api/stores"]

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["name"] = html.unescape(location["name"])
            item["street_address"] = item.pop("addr_full")
            item["website"] = response.urljoin(location["url"])

            # TODO opening hours available as field_open_hours_1_value - field_open_hours_4_value

            yield item
