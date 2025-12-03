from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.structured_data_spider import StructuredDataSpider


class GoApeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "go_ape_gb"
    item_attributes = {"brand": "Go Ape", "brand_wikidata": "Q5574692"}
    sitemap_urls = ["https://goape.co.uk/sitemap-index.xml"]
    sitemap_rules = [(r"https:\/\/goape\.co\.uk\/locations\/([-\w]+)/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        item["addr_full"] = item.pop("street_address")
        apply_category({"leisure": "sports_centre", "aerialway": "zip_line"}, item)
        yield item
