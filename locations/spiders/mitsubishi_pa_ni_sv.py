import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class MitsubishiPANISVSpider(scrapy.Spider):
    name = "mitsubishi_pa_ni_sv"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = [
        "https://mitsubishipanama.com/nuestras-agencias/",
        "https://mitsubishi-motors.com.ni/nuestras-agencias/",
        "https://mitsubishi.com.sv/nuestras-agencias/",
    ]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@data-elementor-post-type="page"]//*[@class="e-con-inner"]'):
            item = Feature()
            if branch := location.xpath(".//h3"):
                item["branch"] = branch.xpath("normalize-space()").get()
                item["addr_full"] = location.xpath('.//*[@data-widget_type="text-editor.default"]//p/text()').get()
                item["phone"] = location.xpath('.//*[@data-widget_type="text-editor.default"]//p[2]/text()').get()
                item["email"] = location.xpath('.//*[@data-widget_type="text-editor.default"]//p[4]/text()').get()
                if "mitsubishipanama" in response.url:
                    item["country"] = "PA"
                elif ".ni" in response.url:
                    item["country"] = "NI"
                elif ".sv" in response.url:
                    item["country"] = "SV"
                if location.xpath(".//@title").get():
                    if m := re.match(r"(-?\d.\d+),\s*(-?\d+.\d+)", location.xpath(".//@title").get()):
                        item["lat"], item["lon"] = m.groups()
                apply_category(Categories.SHOP_CAR, item)
                yield item
