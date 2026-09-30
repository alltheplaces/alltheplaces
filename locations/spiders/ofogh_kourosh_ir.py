from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class OfoghKouroshIRSpider(Spider):
    """Ofogh Kourosh, Iran's largest supermarket chain (okcs.com).

    All branches are server-rendered on a single /stores page as <li>
    elements carrying data-lat/data-lng/address attributes, grouped per
    province. The source exposes no per-store ids, so coordinates double
    as the ref.
    """

    name = "ofogh_kourosh_ir"
    item_attributes = {"brand": "Ofogh Kourosh", "brand_wikidata": "Q65199490"}
    allowed_domains = ["okcs.com"]
    start_urls = ["https://okcs.com/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for province in response.xpath('//ul[@class="states_tmp"]'):
            state = province.xpath("./@state_name").get()
            for store in province.xpath('./li[starts-with(@class, "main_")]'):
                lat = store.xpath("./@data-lat").get()
                lon = store.xpath("./@data-lng").get()
                if not lat or not lon:
                    continue
                item = Feature()
                item["ref"] = f"{lat},{lon}"
                item["name"] = (store.xpath("./text()").get() or "").strip()
                item["addr_full"] = store.xpath("./@address").get()
                item["lat"] = float(lat)
                item["lon"] = float(lon)
                item["state"] = state
                apply_category(Categories.SHOP_SUPERMARKET, item)
                yield item
