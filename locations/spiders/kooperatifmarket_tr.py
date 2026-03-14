from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class KooperatifmarketTRSpider(Spider):
    name = "kooperatifmarket_tr"
    item_attributes = {"brand": "Türkiye Tarım Kredi Kooperatif Market", "brand_wikidata": "Q127328776"}
    start_urls = ["https://www.kooperatifmarket.com.tr/api/stores"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json():
            item = Feature()
            item["ref"] = item["branch"] = poi["marketAdi"]
            item["state"] = poi["marketIl"]
            item["extras"]["addr:district"] = poi["marketIlce"]
            item["lat"] = float(poi["marketEnlem"])
            item["lon"] = float(poi["marketBoylam"])
            item["addr_full"] = poi["marketAdres"]
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
