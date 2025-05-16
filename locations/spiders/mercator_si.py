import html

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MercatorSISpider(SitemapSpider, StructuredDataSpider):
    name = "mercator_si"
    item_attributes = {"brand": "Mercator", "brand_wikidata": "Q738412"}
    allowed_domains = ["www.mercator.si"]
    sitemap_urls = ["https://www.mercator.si/sitemap.xml"]
    sitemap_follow = ["/Store/"]
    sitemap_rules = [(r"^https:\/\/www\.mercator\.si\/prodajna-.*/.*/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    search_for_facebook = False
    search_for_twitter = False
    search_for_email = False

    def post_process_item(self, item, response: Response, ld_data, **kwargs):
        if item["website"] == "https://www.mercator.si/prodajna-mesta/page-6/":
            return

        if name := item.get("name"):
            label = html.unescape(name).upper()
            if "HIPERMARKET" in label or "SUPERMARKET" in label:
                apply_category(Categories.SHOP_SUPERMARKET, item)
                item["name"] = None
            elif "MARKET" in label:
                apply_category(Categories.SHOP_CONVENIENCE, item)
                item["name"] = None
            elif "TRGOVSKI CENTER" in label or "MERCATOR CENTER" in label:
                return  # Some kind of department inside the supermarkets
            elif "CASH" in label:
                apply_category(Categories.SHOP_WHOLESALE, item)
                item["name"] = "Cash & Carry"
            elif "CENTER TEH" in label:
                apply_category(Categories.SHOP_DOITYOURSELF, item)
                item["name"] = "Center Tehnike"

        yield item
