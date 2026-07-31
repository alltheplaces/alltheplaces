from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class LiquorlandNZSpider(SitemapSpider, StructuredDataSpider):
    name = "liquorland_nz"
    item_attributes = {"brand": "Liquorland", "brand_wikidata": "Q110295342"}
    sitemap_urls = ["https://www.liquorland.co.nz/content/sitemaps/sitemap-index.xml"]
    sitemap_rules = [(r"https://www.liquorland.co.nz/store-locations/[^/]+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = item.pop("street_address")
        item["branch"] = item.pop("name").replace("Liquorland ", "")
        item["website"] = response.url
        oh = OpeningHours()
        oh.add_ranges_from_string(",".join(ld_data.get("openingHours")))
        item["opening_hours"] = oh
        yield item
