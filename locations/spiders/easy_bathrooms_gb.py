import re
from typing import Any

import chompjs
from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class EasyBathroomsGBSpider(Spider):
    name = "easy_bathrooms_gb"
    item_attributes = {"brand": "Easy Bathrooms", "brand_wikidata": "Q114348566"}
    allowed_domains = ["www.easybathrooms.com"]
    start_urls = ["https://www.easybathrooms.com/our-showrooms"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for lat, lon, popup in re.findall(
            r"lat: (-?\d+\.\d+),.+?lng: (-?\d+\.\d+),.+?\(({.+?})\);", response.text, re.DOTALL
        ):
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon
            sel = Selector(text=chompjs.parse_js_object(popup)["content"])
            item["ref"] = item["website"] = response.urljoin(sel.xpath("//a/@href").get())
            item["branch"] = sel.xpath("//a/text()").get()
            item["addr_full"] = merge_address_lines(sel.xpath("//div/p/text()").getall())
            yield item
