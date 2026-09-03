from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class ShopMetroPHSpider(Spider):
    name = "shop_metro_ph"
    item_attributes = {"brand_wikidata": "Q23808789"}
    start_urls = ["https://shopmetro.ph/documentation/mrc-member-guide/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for row in response.css("table.store-tbl tbody tr"):
            name = row.css("td.td-name::text").get("").strip()
            if name.startswith("Super Metro "):
                brand = "Super Metro"
                branch = name.removeprefix("Super Metro ")
            else:
                brand = "Metro Supermarket"
                branch = name.removeprefix("Metro ")
            item = Feature(ref=name, brand=brand, branch=branch, addr_full=row.css("td.td-addr::text").get("").strip())
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
