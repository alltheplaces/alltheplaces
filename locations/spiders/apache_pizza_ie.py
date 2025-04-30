from typing import Any

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ApachePizzaIESpider(Spider):
    name = "apache_pizza_ie"
    item_attributes = {"brand": "Apache Pizza", "brand_wikidata": "Q22031794"}
    start_urls = ["https://apache.ie/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield FormRequest(
            url="https://apache.ie/General/GetFilteredStores/",
            formdata={"includeSliceStores": "true"},
            headers={
                "RequestVerificationToken": response.xpath('//input[@id="completeAntiForgeryToken"]/@value').get()
            },
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = merge_address_lines([location["address_line_1"], location["address_line_2"]])
            item["website"] = response.urljoin(location["details_url"])

            yield item
