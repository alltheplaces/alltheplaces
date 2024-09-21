import html
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class RageZA(JSONBlobSpider):
    name = "rage_za"
    item_attributes = {
        "brand": "Rage",
        "brand_wikidata": "Q116377890",
    }

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://shop.ragesa.co.za/ragesa/wp-json/wp/v2/location/?per_page=100&order=asc&page={page}",
            meta={"page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield from self.parse_feature_array(response, response.json())

        if len(response.json()) == 100:
            yield self.make_request(response.meta["page"] + 1)

    def post_process_item(self, item, response, location):
        item["branch"] = html.unescape(item.pop("name")["rendered"])
        if (
            item["branch"].endswith("- SHOES")
            or item["branch"].endswith("– SHOES")
            or item["branch"].endswith("- LADIES SHOES")
            or item["branch"].endswith("– LADIES SHOES")
        ):
            apply_category(Categories.SHOP_SHOES, item)
        elif item["branch"] == "HEAD OFFICE":
            apply_category(Categories.OFFICE_COMPANY, item)
        else:
            apply_category(Categories.SHOP_CLOTHES, item)

        item["addr_full"] = clean_address(location["locationname"])
        yield item
