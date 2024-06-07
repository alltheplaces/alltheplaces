from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BerlinDonerKebapPLSpider(Spider):
    name = "berlin_doner_kebap_pl"
    item_attributes = {
        "brand": "Berlin Döner Kebap",
        "brand_wikidata": "Q126195313",
        "extras": {"amenity": "fast_food", "cuisine": "kebab"},
    }
    start_urls = ["https://www.berlindonerkebap.com/restauracje/wszystkie/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(response.xpath('//script[contains(text(),"gm_data")]/text()').get()):
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["name"]
            item["lat"] = location["lat"]
            item["lon"] = location["long"]
            item["website"] = location["url"]

            sel = Selector(text=location["message"])
            item["addr_full"] = merge_address_lines(sel.xpath("//text()").getall()[1:])

            yield item
