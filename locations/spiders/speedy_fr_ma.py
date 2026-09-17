from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SpeedyFRMASpider(SitemapSpider, StructuredDataSpider):
    name = "speedy_fr_ma"
    item_attributes = {"brand": "Speedy", "brand_wikidata": "Q3492969"}
    sitemap_urls = ["https://centres-auto.speedy.fr/robots.txt"]
    sitemap_rules = [(r"\d+/\d+$", "parse")]
    custom_settings = {"DOWNLOAD_DELAY": 4}
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("lat") is None:
            return

        # overwrite country as the information structured data wrongly indicates country "FR" for locations situated in Morocco.
        if "+212" in (item.get("phone") or "") or (item.get("city") or "") in ["El Jadida", "Mohammedia"]:
            item["country"] = "MA"

        item["branch"] = (item.pop("name", None) or "").removeprefix("Centre Auto SPEEDY ")
        item["image"] = None

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
