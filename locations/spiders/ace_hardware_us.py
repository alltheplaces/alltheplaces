import json
from typing import Any, AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import TextResponse

from locations.items import Feature
from locations.storefinders.kibo import KiboSpider

FETCH_PAGE = """
fetch("/api/commerce/storefront/locationUsageTypes/SP/locations?pageSize=%d&startIndex=%d")
    .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
    })
    .then(d => {
        d.startIndex = d.totalCount;
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(d);
        document.body.appendChild(pre);
    });
"""


class AceHardwareUSSpider(KiboSpider):
    name = "ace_hardware_us"
    item_attributes = {"brand": "Ace Hardware", "brand_wikidata": "Q4672981"}

    def page_request(self, start_index: int) -> Request:
        return Request(
            f"https://www.acehardware.com/store-locator?startIndex={start_index}",
            cb_kwargs={"start_index": start_index},
            meta={
                "zyte_api": {
                    "browserHtml": True,
                    "actions": [
                        {"action": "evaluate", "source": FETCH_PAGE % (self.page_size, start_index)},
                        {"action": "waitForSelector", "selector": {"type": "css", "value": "pre"}, "timeout": 15},
                    ],
                }
            },
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.page_request(0)

    def parse(self, response: TextResponse, start_index: int = 0, **kwargs: Any) -> Iterable[Feature | Request]:
        yield from super().parse(response)
        if start_index == 0:
            total = json.loads(response.xpath("//pre//text()").get())["totalCount"]
            for next_start_index in range(self.page_size, total, self.page_size):
                yield self.page_request(next_start_index)
