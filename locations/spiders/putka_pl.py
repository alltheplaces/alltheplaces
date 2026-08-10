import json
import re
from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PutkaPLSpider(StructuredDataSpider):
    name = "putka_pl"
    item_attributes = {"brand": "Putka", "brand_wikidata": "Q113093586"}
    start_urls = ["https://www.putka.pl/nasze-piekarnie"]
    wanted_types = ["Bakery"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw = response.xpath('//script[@id="bakery-finder-script-js-extra"]/text()').get()
        data = json.loads(re.search(r"var bakeryFinderData = ({.*?});", raw, re.DOTALL).group(1))
        for bakery in data["bakeries"]:
            yield response.follow(bakery["details"]["bakery_link"], callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name")
        item["website"] = response.url
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
