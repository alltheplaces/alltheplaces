import re
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CoteSushiSpider(SitemapSpider, StructuredDataSpider):
    name = "cote_sushi"
    item_attributes = {
        "brand": "Côté Sushi",
        "brand_wikidata": "Q130731390",
    }
    allowed_domains = ["restaurants.cotesushi.com"]
    sitemap_urls = ["https://restaurants.cotesushi.com/sitemap.xml"]
    sitemap_rules = [
        (r"/fr/restaurant-sushi/[^/]+/?$", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image", None)
        item.pop("facebook", None)

        if name := item.pop("name", None):
            item["branch"] = re.sub(
                r"^c[oô]t[ée]\s+sushi\s*(?:-\s*|\s+à\s+)?",
                "",
                name,
                flags=re.IGNORECASE,
            ).strip()

        apply_category(Categories.RESTAURANT, item)
        yield item
