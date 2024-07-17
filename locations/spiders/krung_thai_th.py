import re
from typing import Any

from scrapy import FormRequest, Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class KrungThaiTHSpider(Spider):
    name = "krung_thai_th"
    item_attributes = {"brand_wikidata": "Q962865"}
    start_urls = ["https://krungthai.com/th/contact-us/ktb-location"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield FormRequest(
            url="https://krungthai.com/th/contact-us/getservicelocationresult",
            formdata={"servicePointType": "1"},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "RequestVerificationToken": re.search(r"'RequestVerificationToken': '(.+)' }", response.text).group(1),
            },
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["ListItems"]:
            item = Feature()
            item["ref"] = location["BranchCode"].strip("()").removeprefix("Branch Code ")
            item["branch"] = location["Branch"]
            item["addr_full"] = merge_address_lines(
                Selector(text=location["Address"].split("</div>", 1)[0]).xpath("//text()").getall()
            )
            item["lat"] = location["STR_SERVICE_POINT_MAP_X"]
            item["lon"] = location["STR_SERVICE_POINT_MAP_Y"]

            apply_category(Categories.BANK, item)

            yield item
