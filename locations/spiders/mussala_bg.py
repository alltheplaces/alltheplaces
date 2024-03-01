from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class MussalaBGSpider(Spider):
    name = "mussala_bg"
    item_attributes = {"brand_wikidata": "Q120314195"}
    start_urls = [
        "https://mussalains.com/wp-admin/admin-ajax.php?action=store_search&lat=43.21405&lng=27.914733&autoload=1"
    ]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = merge_address_lines([location.pop("address"), location.pop("address2")])

            yield DictParser.parse(location)
