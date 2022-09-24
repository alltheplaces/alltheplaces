from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class UltaBeautySpider(SitemapSpider, StructuredDataSpider):
    name = "ulta-beauty"
    item_attributes = {"brand": "Ulta-Beauty", "brand_wikidata": "Q7880076"}
    allowed_domains = ["www.ulta.com"]
    sitemap_urls = ("https://www.ulta.com/stores/sitemap.xml",)
    sitemap_rules = [
        (r"/stores/", "parse_sd"),
    ]
    wanted_types = ["Place"]

    def inspect_item(self, item, response):
        # The structured data has bad addressRegion in the JSON but it's OK in the HTML
        item["state"] = response.xpath(
            '//span[@itemprop="addressRegion"]/text()'
        ).extract_first()
        yield item
