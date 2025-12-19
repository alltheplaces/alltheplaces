from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class OxfordLearningSpider(Spider):
    name = "oxford_learning"
    item_attributes = {"name": "Oxford Learning", "brand": "Oxford Learning", "brand_wikidata": "Q124034787"}
    start_urls = ["https://www.oxfordlearning.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(response.xpath('//*[contains(text(),"kh_ld_locations")]/text()').get())[
            0
        ][0]:
            location.update(location.pop("details"))
            item = DictParser.parse(location)
            item["website"] = location["url_en"]
            item["ref"] = location["mis_location_id"]
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address2"], location["address1"]])
            apply_category(Categories.PREP_SCHOOL, item)
            yield item
