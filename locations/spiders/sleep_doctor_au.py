import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SleepDoctorAUSpider(Spider):
    name = "sleep_doctor_au"
    item_attributes = {
        "brand": "Sleep Doctor",
        "name": "Sleep Doctor",
        "brand_wikidata": "Q122435030",
    }
    allowed_domains = ["sleepdoctor.com.au"]
    start_urls = ["https://sleepdoctor.com.au/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield response.follow(url=response.xpath('//script[@type="module"]/@src').get(), callback=self.parse_locations)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(re.search(r"\[{location_name.+?]", response.text).group(0)):
            location["city"] = location.pop("location_name")
            item = DictParser.parse(location)
            item["ref"] = item["website"]
            apply_category(Categories.SHOP_BED, item)
            # Individual store urls don't follow a consistent HTML, which makes it difficult to scrape additional location details such as the full address.
            yield item
