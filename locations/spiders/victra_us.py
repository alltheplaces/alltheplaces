import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class VictraUSSpider(SitemapSpider):
    name = "victra_us"
    item_attributes = {
        "brand": "Verizon",
        "brand_wikidata": "Q919641",
        "operator": "Victra",
        "operator_wikidata": "Q118402656",
    }
    sitemap_urls = ["https://victra.com/robots.txt"]
    sitemap_follow = ["stores-sitemap"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()

        data = json.loads(re.search(r'"locations":\[(.+?)\]};', response.text).group(1))

        branch = data["store"]
        if "-" in branch:
            branch = branch.split("-", 1)[1]

        item["website"] = response.url
        item["branch"] = branch
        item["street_address"] = merge_address_lines([data["address"], data["address2"]])
        item["city"] = data["city"]
        item["state"] = data["state"]
        item["postcode"] = data["zip"]
        item["lat"] = data["lat"]
        item["lon"] = data["lng"]
        item["ref"] = str(data["id"])

        yield item
