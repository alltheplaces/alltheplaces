import json

import chompjs
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HomeDepotSpider(CrawlSpider, StructuredDataSpider):
    name = "home_depot"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["www.homedepot.com"]
    start_urls = ["https://www.homedepot.com/l/storeDirectory"]
    rules = [
        Rule(LinkExtractor(allow=r"^https:\/\/www.homedepot.com\/l\/..$")),
        Rule(LinkExtractor(allow=r"^https:\/\/www.homedepot.com\/l\/.*\/\d*$"), callback="parse_sd"),
    ]
    requires_proxy = "US"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        # There's a JSON blob in the HTML that has a "nearby stores" query that includes lat/lon for this store
        data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "__APOLLO_STATE__")]/text()').get())[
            "ROOT_QUERY"
        ]

        # The key with store info in it seems to change based on store ID, so look for the one we care about
        # It starts with "storeSearch".
        store_info = None
        for k, v in data.items():
            if k.startswith("storeSearch"):
                store_info = v
                break

        if not store_info:
            self.logger.warn("No store_info JSON found in %s", json.dumps(data))
            yield item

        store_info = store_info["stores"][0]

        item["lat"] = store_info["coordinates"]["lat"]
        item["lon"] = store_info["coordinates"]["lng"]

        item["opening_hours"] = OpeningHours()
        for day, info in store_info["storeHours"].items():
            if day == "__typename":
                continue

            item["opening_hours"].add_range(day, info["open"], info["close"])

        yield item
