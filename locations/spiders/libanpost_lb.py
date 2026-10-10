from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class LibanpostLBSpider(Spider):
    name = "libanpost_lb"
    item_attributes = {"operator": "LibanPost", "operator_wikidata": "Q12061157"}
    allowed_domains = ["www.libanpost.com"]
    # The branch picker <select> carries the coordinates; the "Locate us" list below it the addresses.
    start_urls = ["https://www.libanpost.com/english/tools-support/where-are-we"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        addresses = {}
        for box in response.css("div.locateBox div.col-md-4"):
            name = box.css("h5::text").get("").strip()
            address = " ".join(t.strip() for t in box.xpath("./text()").getall() if t.strip())
            if name and address:
                addresses[name] = address
        for option in response.css("select option[data-lat]"):
            name = option.css("::text").get("").strip()
            item = Feature()
            item["ref"] = option.attrib["value"]
            item["lat"], item["lon"] = option.attrib["data-lat"], option.attrib["data-long"]
            item["branch"] = name.removesuffix(" - Post Office").strip()
            item["addr_full"] = addresses.get(name)
            apply_category(Categories.POST_OFFICE, item)
            yield item
