import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class PuuiloFISpider(Spider):
    name = "puuilo_fi"
    item_attributes = {"brand": "Puuilo", "brand_wikidata": "Q18689102"}
    start_urls = ["https://www.puuilo.fi/tavaratalot"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//script[@type="text/x-magento-init"][contains(text(), "storeslist")]/text()').get()
        )["*"]["Magento_Ui/js/core/app"]["components"]["storeslist"]["agents"]:
            self.crawler.stats.inc_value("zx/enabled/{}".format(location["enabled"]))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["country"] = location["country_id"]
            yield item
