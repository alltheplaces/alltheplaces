from scrapy.spiders import SitemapSpider

from locations.items import set_closed
from locations.structured_data_spider import StructuredDataSpider


class MoesSouthwestGrillSpider(SitemapSpider, StructuredDataSpider):
    name = "moes_southwest_grill"
    item_attributes = {
        "brand": "Moe's Southwest Grill",
        "brand_wikidata": "Q6889938",
    }
    sitemap_urls = ["https://locations.moes.com/robots.txt"]
    sitemap_rules = [
        (r"locations\.moes\.com/.*/.*/.*$", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if name := item.get("name"):
            if name.endswith("- Temporarily Closed"):
                pass  # TODO?
            elif item["name"].endswith("- Closed"):
                set_closed(item)
            item["branch"] = item.pop("name").removeprefix("Moe's Southwest Grill ")

        yield item
