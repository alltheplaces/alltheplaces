from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JdSportsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "jd_sports_us"
    item_attributes = {"brand": "JD Sports", "brand_wikidata": "Q6108019"}
    sitemap_urls = ["https://stores.jdsports.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+.html$", "parse")]
    wanted_types = ["ShoeStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["branch"] = response.xpath("normalize-space(//h2/text())").get()

        yield item
