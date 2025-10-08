import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class MaidenheadAquaticsGBSpider(Spider):
    name = "maidenhead_aquatics_gb"
    item_attributes = {"brand": "Maidenhead Aquatics", "brand_wikidata": "Q120800751"}
    start_urls = ["https://www.fishkeeper.co.uk/storefinder"]
    custom_settings = {"DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"}}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("//@data-custommage-init").get())["locator"]["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            yield item
