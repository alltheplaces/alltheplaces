import re
from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature


class ZebrosZASpider(Spider):
    name = "zebros_za"
    item_attributes = {"brand": "Zebro's", "brand_wikidata": "Q116619443"}
    allowed_domains = ["www.zebros.co.za"]
    start_urls = ["https://www.zebros.co.za/elementor-page-451/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        js_blob = response.xpath('//script[contains(text(), "tippy(\'*[data-name=")]/text()').get()
        js_blob = js_blob.replace("'+pinsvg+'", "")
        js_blobs_per_store = re.split(r"^\$\('\*\[data-name=", js_blob, flags=re.MULTILINE)
        for js_blob_per_store in js_blobs_per_store[1:]:
            properties = {}
            if m := re.search(r'\[data-name="(.+?)"\]', js_blob_per_store):
                properties["ref"] = m.group(1)
            if m := re.search(r'window.location = "(.+?)";', js_blob_per_store):
                properties["lat"], properties["lon"] = url_to_coords(m.group(1))
            if m := re.search(r"content: '(.+?)',", js_blob_per_store):
                tooltip = Selector(text=m.group(1))
                if branch_name := tooltip.xpath("//h3/text()").get().removeprefix("Zebro's").strip():
                    properties["branch"] = branch_name
                properties["addr_full"] = tooltip.xpath("//p/text()").get()
                properties["phone"] = tooltip.xpath('//a[contains(@href, "tel:")]/@href').get().removeprefix("tel:")
            apply_category(Categories.FAST_FOOD, properties)
            yield Feature(**properties)
