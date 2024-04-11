from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OreillyAutoSpider(SitemapSpider, StructuredDataSpider):
    name = "oreilly"
    item_attributes = {"brand": "O'Reilly Auto Parts", "brand_wikidata": "Q7071951", "country": "US"}
    allowed_domains = ["locations.oreillyauto.com"]
    sitemap_urls = ["https://locations.oreillyauto.com/sitemap.xml"]
    sitemap_rules = [(r"autoparts-([0-9]+).html$", "parse_sd")]
    wanted_types = ["AutoPartsStore"]
    search_for_twitter = False
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["extras"]["website:en"] = response.url
        item["extras"]["website:es"] = response.xpath('//a[@class="translate-link ga-link"]/@href').get()
        item["facebook"] = (
            response.xpath('//a[@class="ga-link"][contains(@href, "https://www.facebook.com/")]/@href').get() or ""
        ).removesuffix("/reviews/?ref=page_internal")

        yield item
