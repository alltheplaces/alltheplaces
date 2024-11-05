import json
import re
from typing import Any

import scrapy
from scrapy import Selector
from scrapy.http import Response

from locations.dict_parser import DictParser


class LeylandSdmGBSpider(scrapy.Spider):
    name = "leyland_sdm_gb"
    item_attributes = {"brand": "Leyland SDM", "brand_wikidata": "Q110437963"}
    start_urls = ["https://leylandsdm.co.uk/amlocator/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(
            re.search(
                r"items\":(\[.*\]),\"totalRecords", response.xpath('//*[contains(text(),"jsonLocations")]/text()').get()
            ).group(1)
        )
        for store in data:
            html_data = Selector(text=store["popup_html"])
            item = DictParser.parse(store)
            item["name"] = html_data.xpath("//h3//text()").get()
            item["street_address"] = html_data.xpath("//text()[4]").get().replace("Address:", "")
            item["city"] = html_data.xpath("//text()[5]").get().replace("City:", "")
            item["postcode"] = html_data.xpath("//text()[6]").get().replace("Postcode:", "")
            item["phone"] = html_data.xpath("//text()[7]").get()
            item["website"] = html_data.xpath("//@href").get().replace("Maida Vale/", "Maida%20Vale/")
            yield item
