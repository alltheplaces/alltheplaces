import json
from typing import Any

from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider


class RymanGBSpider(JSONBlobSpider):
    name = "ryman_gb"
    item_attributes = {"brand": "Ryman", "brand_wikidata": "Q7385188"}
    start_urls = ["https://www.ryman.co.uk/storefinder/"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Host": "www.ryman.co.uk"}}
    requires_proxy = True
    drop_attributes = {"facebook", "twitter"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath('//script[@type="text/x-magento-init"]//text()').getall()
        for script in scripts:
            if "locations" in script:
                result = json.loads(script)
                for store in DictParser.get_nested_key(result, "locations"):
                    item = DictParser.parse(store)
                    item["lat"] = store["latitude"]
                    item["lon"] = store["longitude"]
                    item["branch"] = item.pop("name")
                    item["street_address"] = item.pop("addr_full")
                    yield item
