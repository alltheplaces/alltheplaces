from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FurnmartSpider(Spider):
    name = "furnmart"
    item_attributes = {"brand": "Furnmart", "brand_wikidata": "Q118185771"}
    countries = {
        "https://www.furnmart.co.bw": "fm-bwa",
        "https://www.furnmart.com.na": "fm-nam",
        "https://www.furnmart.co.za": "fm-rsa",
    }

    async def start(self) -> Any:
        for base, namespace in self.countries.items():
            yield JsonRequest(
                url=f"{base}/api/cms/fetch?path=%2Fapi%2Fcontent%2F{namespace}%2Fstore",
                meta={"base": base},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("items", []):
            data = location.get("data", {})
            slug = data.get("slug", {}).get("iv")
            if not slug:
                continue
            item = Feature()
            item["branch"] = data.get("title", {}).get("iv", "").title() or None
            item["ref"] = item["website"] = f"{response.meta['base']}/stores/{slug}"
            item["phone"] = data.get("telephone", {}).get("iv")
            item["street_addreess"] = clean_address(
                [data.get("adressStreet", {}).get("iv"), data.get("adressStreet2", {}).get("iv")]
            )

            if coords := data.get("addressCoordinates", {}).get("iv"):
                item["lat"] = coords.get("latitude")
                item["lon"] = coords.get("longitude")

            apply_category(Categories.SHOP_FURNITURE, item)

            yield item
