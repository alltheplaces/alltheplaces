from json import loads
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NewBalanceGBSpider(SitemapSpider, StructuredDataSpider):
    name = "new_balance_gb"
    item_attributes = {"brand": "New Balance", "brand_wikidata": "Q742988"}
    sitemap_urls = ["https://stores.newbalance.co.uk/sitemap1.xml"]
    sitemap_rules = [(r"^https:\/\/stores\.newbalance\.co\.uk\/[\w-]+/[\w-]+$", "parse_sd")]
    drop_attributes = {"facebook"}
