from scrapy import Spider

from locations.dict_parser import DictParser


class UltraTuneAUSpider(Spider):
    name = "ultra_tune_au"
    item_attributes = {"brand": "Ultra Tune", "brand_wikidata": "Q29025649"}
    start_urls = ["https://www.ultratune.com.au/wp-admin/admin-ajax.php?action=asl_load_stores"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = location.pop("street")

            yield DictParser.parse(location)
