from phpserialize import unserialize
from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class StaterBrosUSSpider(Spider):
    name = "stater_bros_us"
    item_attributes = {"brand": "Stater Bros.", "brand_wikidata": "Q7604016"}
    allowed_domains = ["www.staterbros.com"]
    start_urls = ["https://www.staterbros.com/wp-json/api/stores/"]

    def parse(self, response):
        locations = StaterBrosUSSpider._replace_horrible_api_output(response.json())
        for store_id, location in locations.items():
            item = DictParser.parse(location)
            item["ref"] = store_id
            item["website"] = "https://www.staterbros.com/stores/" + store_id
            item["opening_hours"] = OpeningHours()
            hours_string = " ".join(
                filter(None, map(str.strip, Selector(text=location["store_hours"]).xpath("//text()").getall()))
            )
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item

    @staticmethod
    def _replace_horrible_api_output(unidentified_cruft: dict) -> dict:
        """
        :param unidentified_cruft: a dictionary of unexplainable
                                   horrors.
        :returns: a dictionary that any other sane API might return
                  instead.
        """
        locations = {}
        for bizarre_object in unidentified_cruft:
            store_id = bizarre_object["store_number"]
            if bizarre_object["store_number"] not in locations.keys():
                locations[store_id] = {}
            locations[store_id][bizarre_object["meta_key"]] = bizarre_object["meta_value"]
        for store_id, location in locations.items():
            # Reference: https://www.php.net/manual/en/function.unserialize.php
            php_serialized_string = location["map"].encode("utf-8")
            unserialized_object = unserialize(php_serialized_string)
            unserialized_dict = {
                k.decode(): v.decode() if isinstance(v, bytes) else v for k, v in unserialized_object.items()
            }
            location.update(unserialized_dict)
            location.pop("map")
        return locations
