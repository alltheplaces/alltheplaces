# this is very dependent ono the structure of the page not changing
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class LyleAndScottSpider(Spider):
    name = "lyle_and_scott"
    item_attributes = {"brand": "Lyle & Scott", "brand_wikidata": "Q3269443"}
    start_urls = ["https://www.lyleandscott.com/pages/our-stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.xpath("//section")
        for location in data:
            item = Feature()
            item["ref"] = location.xpath("@aria-labelledby").get()
            if item["ref"]:
                item["ref"] = item["ref"].replace("section-title-template--23830581313916__", "")
            item["name"] = "Lyle & Scott"
            item["branch"] = location.xpath("div/div/div/h2/text()").get()
            if item["branch"]:
                item["branch"] = re.sub(r"\n", "", item["branch"]).strip()
            else:
                continue
            address = " ".join(location.xpath("div/div/div/div/p").getall())
            address = re.sub(r"(<p>|</p>|<br>|\u202f|\u2028)", "", address)
            if "Tel: " in address:
                item["addr_full"], item["phone"] = address.split("Tel: ")
            else:
                item["addr_full"] = address
            coords = location.xpath("div/div/div/a/@href").get()
            if coords:
                m = re.search(r"https://www.google.com/maps/place/[^/]+/@([^,]+),([^,]+),", coords)
                item["lat"], item["lon"] = m.group(1), m.group(2)
            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
