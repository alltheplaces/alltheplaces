from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class NewLookGBSpider(SitemapSpider, StructuredDataSpider):
    name = "new_look_gb"
    item_attributes = {"brand": "New Look", "brand_wikidata": "Q12063852"}
    sitemap_urls = ["https://www.newlook.com/uk/sitemap/maps/sitemap_uk_pos_en_1.xml"]
    sitemap_rules = [(r"https:\/\/www\.newlook\.com\/uk\/store\/[-\w]+-(\d+)$", "parse_sd")]
    wanted_types = ["Store"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "closed" not in entry["loc"].lower():
                yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.urljoin(item["website"])
        yield item
