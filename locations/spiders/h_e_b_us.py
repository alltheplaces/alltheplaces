from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HEBUSSpider(SitemapSpider, StructuredDataSpider):
    name = "h_e_b_us"
    HEB = {"brand": "H-E-B", "brand_wikidata": "Q830621"}
    HEB_PLUS = {"brand": "H-E-B plus!", "brand_wikidata": "Q830621"}
    allowed_domains = ["www.heb.com"]
    sitemap_urls = ["https://www.heb.com/sitemap/storeSitemap.xml"]
    download_delay = 5

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "H-E-B plus!" in item["name"]:
            item.update(self.HEB_PLUS)
        elif "H-E-B" in item["name"]:
            item.update(self.HEB)

        yield item
