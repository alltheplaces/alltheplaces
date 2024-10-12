import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class OldWildWestSpider(Spider):
    name = "old_wild_west"
    item_attributes = {"brand": "Old Wild West", "brand_wikidata": "Q25402475"}
    start_urls = ["https://www.oldwildwest.it/ristoranti"]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//input[@id="map_data"]/@value').get()):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Old Wild West ")  # Title
            item["website"] = response.urljoin(location["url"])
            item["ref"] = location["rNode"]
            item["addr_full"] = merge_address_lines([location["Indirizzo"], location["Localita"]])
            item["email"] = location["eMail"]

            apply_yes_no(Extras.DELIVERY, item, location.get("IsDeliveryEnabled") is True)
            apply_yes_no(Extras.DELIVERY, item, location.get("IsTakeAwayEnabled") is True)

            yield item
