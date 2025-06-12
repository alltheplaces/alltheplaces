import scrapy

from locations.dict_parser import DictParser


class EuromobilNLSpider(scrapy.Spider):
    name = "euromobil_nl"
    item_attributes = {"brand": "Euromobil", "brand_wikidata": "Q1375118"}
    start_urls = ["https://euromobil.nl/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            yield item
