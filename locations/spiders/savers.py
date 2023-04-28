import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SaversSpider(SitemapSpider, StructuredDataSpider):
    name = "savers"
    item_attributes = {"brand": "Savers", "brand_wikidata": "Q7428188"}
    allowed_domains = ["stores.savers.com", "stores.savers.com.au"]
    sitemap_urls = [
        "https://stores.savers.com/sitemap/sitemap_index.xml",
        "https://stores.savers.com.au/sitemap/sitemap_index.xml",
    ]
    sitemap_rules = [
        (
            r"(?<!community-donation-center-\d{4})(?<!donation-drop-spot-\d{4})\.html$",
            "parse_sd",
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        item["ref"] = re.search(r"-(\d{4})\.html$", response.url).group(1)
        item["name"] = response.xpath('//div[contains(@class, "location-name")]/text()').get().strip()
        item["brand"] = (
            response.xpath("//@data-brand").get().replace("Savers AU", "Savers").replace("Boutique", "Savers")
        )
        item.pop("image")
        item.pop("facebook")
        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
