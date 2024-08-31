from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class YbsGBSpider(Spider):
    name = "ybs_gb"
    item_attributes = {"brand": "Yorkshire Building Society", "brand_wikidata": "Q12073381"}
    start_urls = ["https://www.ybs.co.uk/assets/ybs-location-data.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if store["Type"] == "Agency":
                continue
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["ref"] = item["website"] = (
                "https://www.ybs.co.uk/contact-us/branch-finder/details.html?location={}&type={}".format(
                    store["URL"], store["Type"]
                )
            )
            item["addr_full"] = merge_address_lines(
                [store[f] if store[f] != "0" else None for f in ["Address1", "Address2", "Address3", "Postcode"]]
            )

            # TODO Opening hours

            apply_category(Categories.BANK, item)

            yield item
