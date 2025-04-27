from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.items import Feature


# Sitemap is incomplete - 534 shops but only 218 on sitemap
# No location available
class CancerResearchUkGBSpider(Spider):
    name = "cancer_research_uk_gb"
    item_attributes = {"brand": "Cancer Research UK", "brand_wikidata": "Q326079", "country": "GB"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://xss-content.ent.eu-west-1.aws.found.io/api/as/v1/engines/shops/search.json",
            data={
                "query": "",
                "result_fields": {
                    "title": {"raw": {}},
                    "url": {"raw": {}},
                    "postcode": {"raw": {}},
                    "shop_address": {"raw": {}},
                    "shop_phone_number": {"raw": {}},
                    "document_type": {"raw": {}},
                    "content_type": {"raw": {}},
                    "postcode_location": {"raw": {}},
                },
                "search_fields": {
                    "postcode": {},
                    "title": {},
                    "shop_address": {},
                    "shop_phone_number": {},
                    "postcode_location": {},
                },
                "page": {"size": 100, "current": page},
            },
            headers={"Authorization": "Bearer search-yxrzepvos3f259zqovdykpmf"},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["results"]:
            item = Feature()
            item["addr_full"] = location["shop_address"]["raw"]
            item["phone"] = location.get("shop_phone_number", {}).get("raw")
            item["postcode"] = location["postcode"]["raw"]
            item["branch"] = location["title"]["raw"]
            item["website"] = location["url"]["raw"]
            item["ref"] = location["id"]["raw"]

            yield item

        page = response.json()["meta"]["page"]
        if page["current"] <= page["total_pages"]:
            yield self.make_request(page["current"] + 1)
