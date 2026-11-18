from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class VeneziasPizzeriaUSSpider(StructuredDataSpider):
    name = "venezias_pizzeria_us"
    start_urls = ["https://venezias.com/locations/"]
    wanted_types = ["Restaurant"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # One location is linked both with and without its trailing slash, and the
        # two spellings would otherwise be crawled as two separate locations.
        urls = {url.rstrip("/") + "/" for url in response.xpath('//a[contains(@href, "/location/")]/@href').getall()}
        for url in urls:
            yield response.follow(url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = ld_data.get("branchCode")
        # Six locations are named "Venezia's Pizzeria - <branch>"; the ASU campus
        # shop trades under the chain's express name instead and names no branch.
        brand, separator, branch = item.pop("name", "").partition(" - ")
        item["brand"] = brand or None
        item["branch"] = branch or None

        # The social accounts are the chain's own, repeated identically on every
        # page, and the photos are unreliable: the express shop shows the Tempe
        # store and one Mesa page shows the other Mesa store.
        item["image"] = item["twitter"] = item["facebook"] = None

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"
        yield item
