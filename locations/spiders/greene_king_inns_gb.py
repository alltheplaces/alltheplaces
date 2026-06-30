from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class GreeneKingInnsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "greene_king_inns_gb"
    item_attributes = {"brand": "Greene King", "brand_wikidata": "Q5564162"}
    sitemap_urls = ["https://www.greenekinginns.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.greenekinginns\.co\.uk\/hotels\/[\w\-]+\/[\w\-]+$", "parse_sd")]
    wanted_types = ["Hotel"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["ref"].replace("gki-", "")

        apply_category(Categories.HOTEL, item)

        yield item
