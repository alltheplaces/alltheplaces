from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SephoraPLSpider(SitemapSpider, StructuredDataSpider):
    name = "sephora_pl"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    sitemap_urls = [
        "https://www.sephora.pl/sitemap-store-locator.xml",
    ]

    user_agent = BROWSER_DEFAULT
    require_proxy = True

    def post_process_item(self, item, response, ld_data):
        item.pop("image")
        hours_string = " ".join(ld_data["openingHours"])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
