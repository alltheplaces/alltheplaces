import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, DAYS_EN, day_range


def days_of(text: str) -> list[str]:
    # "Mon - Fri", "Monday - Sunday", "Sat", "Sunday"
    names = [DAYS_EN[d.title()] for d in re.findall(rf"\b({'|'.join(DAYS_3_LETTERS)})[a-z]*", text, re.I)]
    if len(names) >= 2 and "-" in text:
        return day_range(names[0], names[1])
    return names


class IomPostIMSpider(Spider):
    name = "iom_post_im"
    item_attributes = {"operator": "Isle of Man Post Office", "operator_wikidata": "Q3432267"}
    allowed_domains = ["www.iompost.com"]

    def make_request(self, page: int) -> Request:
        return Request(
            f"https://www.iompost.com/api/customer-touch-points?fields%5B1%5D=Name&fields%5B2%5D=TouchPointType&fields%5B5%5D=Location&pagination%5Bpage%5D={page}&pagination%5BpageSize%5D=100",
        )

    async def start(self) -> AsyncIterator[Any]:
        yield self.make_request(1)

    def parse(self, response: Response) -> Any:
        for location in response.json().get("data"):
            item = DictParser.parse(location)
            if lat_lon := location.get("Location"):
                item["lon"], item["lat"] = lat_lon.get("geometry").get("coordinates")
            apply_category(Categories.POST_OFFICE, item)
            yield item
        current_page = response.json().get("meta").get("pagination").get("page")
        total_page = response.json().get("meta").get("pagination").get("pageCount")
        if current_page <= total_page:
            yield self.make_request(current_page + 1)
