import re

import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class MetaSpider(Spider):
    name = "meta"
    item_attributes = {"brand": "Meta", "brand_wikidata": "Q380"}
    start_urls = ["https://www.metacareers.com/locations"]

    def parse(self, response, **kwargs):
        script = response.xpath('//script[contains(text(), "jobCount")]/text()').get()
        blob = re.search(r"handle\((.+)\);", script)
        data = chompjs.parse_js_object(blob.group(1))

        for location in DictParser.get_nested_key(data, "locations"):
            item = Feature()
            item["ref"] = item["website"] = response.urljoin(location["locationURI"])
            item["branch"] = location["displayName"]
            item["lon"], item["lat"] = location["coordinates"]

            if location["isDataCenter"]:
                apply_category(Categories.DATA_CENTRE, item)
            else:
                apply_category(Categories.OFFICE_IT, item)

            yield item
