from typing import Iterable

from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GridserveGBSpider(JSONBlobSpider):
    name = "gridserve_gb"
    item_attributes = {"operator": "Gridserve", "operator_wikidata": "Q89575318"}
    allowed_domains = ["dnms-api.gridserve.com", "electrichighway.gridserve.com"]
    start_urls = ["https://dnms-api.gridserve.com/api/v1/locations/1/All?searchText=&sort=&orderType=asc"]
    locations_key = "data"

    def start_requests(self) -> Iterable[Request]:
        yield Request(url="https://electrichighway.gridserve.com/", callback=self.parse_js_files)

    def parse_js_files(self, response: Response) -> Iterable[Request]:
        js_blob = response.xpath('//script[contains(text(), ":static/chunks/app/page-")]/text()').get()
        page_js_id = js_blob.split(":static/chunks/app/page-", 1)[1].split(".js", 1)[0]
        page_js_url = f"https://electrichighway.gridserve.com/_next/static/chunks/app/page-{page_js_id}.js"
        yield Request(url=page_js_url, callback=self.parse_auth_token)

    def parse_auth_token(self, response: Response) -> Iterable[JsonRequest]:
        auth_token = "eyJ" + response.text.split('="eyJ', 1)[1].split('"', 1)[0]
        yield JsonRequest(url=self.start_urls[0], headers={"Authorization": f"Bearer {auth_token}"})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        apply_category(Categories.CHARGING_STATION, item)
        yield item
