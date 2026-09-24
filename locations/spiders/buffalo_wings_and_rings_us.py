import re
from datetime import datetime
from typing import Any, Iterable
from urllib.parse import urlparse

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BuffaloWingsAndRingsUSSpider(StructuredDataSpider):
    name = "buffalo_wings_and_rings_us"
    item_attributes = {"brand": "Buffalo Wings & Rings", "brand_wikidata": "Q4985900"}
    allowed_domains = ["www.wingsandrings.com"]
    start_urls = ["https://www.wingsandrings.com/locations/"]
    json_parser = "chompjs"

    def parse(self, response: Response) -> Iterable[Request]:
        for url in set(response.css('a[href*="/locations/"]::attr(href)').getall()):
            path = urlparse(response.urljoin(url)).path.rstrip("/")
            if re.fullmatch(r"/locations/[^/]+", path):
                yield response.follow(url, callback=self.parse_sd)

    def pre_process_data(self, ld_data: dict, **kwargs: Any) -> None:
        for rule in ld_data.get("openingHoursSpecification", []):
            for key in ("opens", "closes"):
                if not (raw_time := rule.get(key)):
                    continue
                for time_format in ("%I:%M%p", "%I%p"):
                    try:
                        rule[key] = datetime.strptime(raw_time.upper(), time_format).strftime("%H:%M")
                        break
                    except ValueError:
                        continue

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        if item["country"] != "US":
            return

        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item["city"]
        item.pop("name", None)
        apply_category(Categories.RESTAURANT, item)
        yield item
