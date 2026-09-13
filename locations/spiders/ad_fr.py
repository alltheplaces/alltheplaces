from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AdFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ad_fr"
    item_attributes = {"brand": "AD", "brand_wikidata": "Q108753388"}
    sitemap_urls = ["https://www.ad.fr/sitemap.xml"]
    sitemap_rules = [(r"/garage/[^/]+$", "parse")]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        branch = item.pop("name", "") or ""
        # Page <title> is "<branch name> - <city> (<postcode>)[ | <suffix>]"; strip that tail.
        postcode = item.get("postcode")
        if postcode and (idx := branch.rfind(" - ")) != -1 and postcode in branch[idx:]:
            branch = branch[:idx]
        item["branch"] = branch

        # Source tags New Caledonia stores as "FR"; its own ISO 3166-1 code is "NC".
        if postcode and postcode.startswith("988"):
            item["country"] = "NC"

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
