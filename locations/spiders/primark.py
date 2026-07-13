import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import FIREFOX_LATEST


class PrimarkSpider(SitemapSpider, StructuredDataSpider):
    name = "primark"
    item_attributes = {"brand": "Primark", "brand_wikidata": "Q137023"}
    sitemap_urls = ["https://www.primark.com/robots.txt"]
    sitemap_rules = [
        # Root sitemap should be a sitemap index, normal sitemap
        ("sitemap-store-locator.xml", "_parse_sitemap"),
        # We need to have languages in here to avoid multilingual duplicates
        (r"/de-at/stores/[^/]+/[^/]+$", "parse"),
        (r"/nl-be/stores/[^/]+/[^/]+$", "parse"),
        (r"/cs-cz/stores/[^/]+/[^/]+$", "parse"),
        (r"/de-de/stores/[^/]+/[^/]+$", "parse"),
        (r"/es-es/stores/[^/]+/[^/]+$", "parse"),
        (r"/fr-fr/stores/[^/]+/[^/]+$", "parse"),
        (r"/en-gb/stores/[^/]+/[^/]+$", "parse"),
        (r"/en-ie/stores/[^/]+/[^/]+$", "parse"),
        (r"/it-it/stores/[^/]+/[^/]+$", "parse"),
        (r"/nl-nl/stores/[^/]+/[^/]+$", "parse"),
        (r"/pl-pl/stores/[^/]+/[^/]+$", "parse"),
        (r"/pt-pt/stores/[^/]+/[^/]+$", "parse"),
        (r"/ro-ro/stores/[^/]+/[^/]+$", "parse"),
        (r"/sl-si/stores/[^/]+/[^/]+$", "parse"),
        (r"/sk-sk/stores/[^/]+/[^/]+$", "parse"),
        (r"/en-us/stores/[^/]+/[^/]+$", "parse"),
    ]
    custom_settings = {"USER_AGENT": FIREFOX_LATEST}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["website"] = response.url
        for k in item.fields.keys():
            if item.get(k) == "{{placeholder}}":
                item[k] = None

        item["branch"] = item.pop("name").removeprefix("Primark ").removeprefix("Penneys ")

        item["state"] = None
        item["country"] = response.url.split("/")[3].split("-")[1]
        if m := re.search(
            r'\\"displayCoordinate\\":{\\"latitude\\":(-?\d+\.\d+),\\"longitude\\":(-?\d+\.\d+)', response.text
        ):
            item["lat"], item["lon"] = m.groups()

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
