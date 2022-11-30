from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HRBlockSpider(SitemapSpider, StructuredDataSpider):
    name = "h_r_block"
    item_attributes = {"brand": "H&R Block", "brand_wikidata": "Q5627799"}
    sitemap_urls = ["https://www.hrblock.com/sitemaps/hrb-opp-sitemap.xml"]
    sitemap_rules = [
        (r"https://www\.hrblock\.com/local-tax-offices/.+/.+/.+/(\d+)/$", "parse_sd")
    ]
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware": None
        }
    }

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        yield item
