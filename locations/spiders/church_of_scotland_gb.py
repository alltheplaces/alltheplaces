from typing import AsyncIterator

import xmltodict
from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ChurchOfScotlandGBSpider(Spider):
    name = "church_of_scotland_gb"
    item_attributes = {"operator": "Church of Scotland", "operator_wikidata": "Q922480"}

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(0)

    def make_request(self, offset: int) -> Request:
        return Request(
            f"https://cos.churchofscotland.org.uk/church-finder/phpsqlsearch_genxml_contacts?latitude=56.06754&longitude=-3.77201&radius=10000000&limit=100&start={offset}",
            cb_kwargs={"offset": offset},
        )

    def parse(self, response, **kwargs):
        data = xmltodict.parse(response.text, attr_prefix="").get("churches", []).get("church", [])
        if data:
            for church in data:
                item = DictParser.parse(church)
                item["name"] = church["church_name"]
                item.pop("website")
                apply_category(Categories.PLACE_OF_WORSHIP, item)
                item["extras"]["religion"] = "christian"
                item["extras"]["denomination"] = "presbyterian"
                yield item
            yield self.make_request(kwargs["offset"] + 50)
