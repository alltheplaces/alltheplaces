import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ChangeGroupSpider(Spider):
    name = "change_group"
    item_attributes = {"brand": "Change Group", "brand_wikidata": "Q5071758"}
    """
        The following Javascript file has the actual API details, being used.
        https://uk.changegroup.com/.resources/ProsegurWebCorpModule/resources/changegroup/branch-locator/main.js
    """
    start_urls = ["https://uksw.changegroup.com/slatwall/?slatAction=changeGroup:main.globalBranchData"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.text.encode("utf-8")
        for country in json.loads(data)["countries"]:
            for region in country["regions"]:
                for location in region["branches"]:
                    item = DictParser.parse(location)
                    item["street_address"] = merge_address_lines(
                        [location["address"].pop("streetAddress"), location["address"].pop("streetAddress2")]
                    )
                    apply_category(Categories.BUREAU_DE_CHANGE, item)
                    yield item
