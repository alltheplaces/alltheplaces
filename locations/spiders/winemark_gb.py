from html import unescape
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class WinemarkGBSpider(Spider):
    name = "winemark_gb"
    item_attributes = {"brand": "Winemark", "brand_wikidata": "Q122011535"}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://winemark.com/wp-admin/admin-ajax.php",
            formdata={"action": "csl_ajax_onload", "radius": "10000"},
        )

    def parse(self, response, **kwargs):
        for location in response.json()["response"]:
            location["street_address"] = unescape(
                merge_address_lines([location.pop("address"), location.pop("address2")])
            )
            item = DictParser.parse(location)
            item["extras"]["branch"] = item.pop("name")
            if url := location["url"]:
                item["website"] = response.urljoin(url)

            yield item
