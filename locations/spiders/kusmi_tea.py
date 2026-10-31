import re
from typing import Any, Iterable

import chompjs
from scrapy import Request
from scrapy.http import Response, TextResponse

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KusmiTeaSpider(StructuredDataSpider):
    name = "kusmi_tea"
    item_attributes = {"brand_wikidata": "Q944186"}
    start_urls = ["https://www.kusmitea.com/pages/trouvez-votre-boutique"]
    wanted_types = ["Store"]
    drop_attributes = {"facebook", "image"}
    custom_settings = {"DOWNLOAD_DELAY": 1}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        stores = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "storesData")]/text()').get().split("storesData =")[1]
        )
        for store in stores:
            if store["storeType"] == "Redistributeur":
                continue
            url = response.xpath(
                f'//*[@data-store-id="{store["id"]}"]//a[contains(@href, "/pages/boutiques/")]/@href'
            ).get()
            yield response.follow(url, self.parse_sd, meta={"ref": store["id"]})

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.meta["ref"]
        item["branch"] = re.sub(r"^Kusmi Tea\s*\|\s*", "", item.pop("name"))
        yield item
