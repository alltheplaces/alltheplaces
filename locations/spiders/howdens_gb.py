import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HowdensGBSpider(SitemapSpider, StructuredDataSpider):
    name = "howdens_gb"
    item_attributes = {"brand_wikidata": "Q5921438"}
    sitemap_urls = ["https://www.howdens.com/sitemap.xml"]
    sitemap_follow = ["depots-find-a-depot"]
    sitemap_rules = [(r"/find-a-depot/([^/]+)", "parse")]
    wanted_types = ["LocalBusiness"]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Howdens - ")
        if m := re.search(r"\[(-?\d+\.\d+),(-?\d+\.\d+)\]", response.text):
            item["lon"], item["lat"] = m.groups()

        yield item
