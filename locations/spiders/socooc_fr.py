import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.structured_data_spider import StructuredDataSpider


class SocoocFRSpider(SitemapSpider, StructuredDataSpider):
    name = "socooc_fr"
    item_attributes = {"brand": "SoCoo'c", "brand_wikidata": "Q62783840"}
    sitemap_urls = ["https://www.socooc.com/sitemap.xml"]
    sitemap_rules = [(r"/magasin/socooc-[^/]+$", "parse_sd")]
    wanted_types = ["Store"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Coordinates are only available embedded in a Google Maps embed URL
        # inside an Angular state JSON blob, not as an iframe/anchor tag, so
        # extract_google_position()'s xpath-based discovery can't find it.
        if m := re.search(r'"virtualTour":\{"url":"(https://www\.google\.com/maps/embed\?pb=[^"]*)"', response.text):
            item["lat"], item["lon"] = url_to_coords(m.group(1))

        apply_category(Categories.SHOP_KITCHEN, item)
        yield item
