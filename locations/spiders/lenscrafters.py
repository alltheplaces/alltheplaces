import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.items import set_closed
from locations.spiders.tesco_gb import set_located_in
from locations.structured_data_spider import StructuredDataSpider


class LenscraftersSpider(SitemapSpider, StructuredDataSpider):
    name = "lenscrafters"
    MACYS = {"brand": "Macy's", "brand_wikidata": "Q629269"}
    item_attributes = {"brand": "LensCrafters", "brand_wikidata": "Q6523209", "extras": Categories.SHOP_OPTICIAN.value}
    sitemap_urls = ["https://local.lenscrafters.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+\.html$", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"{\"latitude\":(-?\d+\.\d+),\"longitude\":(-?\d+\.\d+)}", response.text):
            item["lat"], item["lon"] = m.groups()

        if item["name"].endswith(" - Closed"):
            item["name"] = item["name"].removesuffix(" - Closed")
            set_closed(item)

        if item["name"].endswith(" at Macy's"):
            item["name"] = item["name"].removesuffix(" at Macy's")
            set_located_in(self.MACYS, item)

        yield item
