from datetime import datetime
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT

class MatsukiyoSpider(Spider):
    name = "matsukiyo"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"user-agent": BROWSER_DEFAULT}}    
    start_urls = ["https://www.matsukiyococokara-online.com/map/s3/json/stores.json"]
    allowed_domains = ["www.matsukiyococolara-online.com", "www.matsukiyococokara-online.com"]
    def parse (self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            yield item