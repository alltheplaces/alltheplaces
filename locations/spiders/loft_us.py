from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LoftUSSpider(SitemapSpider, StructuredDataSpider):
    name = "loft_us"
    item_attributes = {"brand": "Loft", "brand_wikidata": "Q62075137"}
    allowed_domains = ["www.loft.com"]
    sitemap_urls = ["https://www.loft.com/sitemap_index.xml"]
    sitemap_rules = [
        (r"/store/outlet/[-\w]{2}/[-\w]+/[-\w]+$", "parse_sd"),
        (r"/store/[-\w]{2}/[-\w]+/[-\w]+$", "parse_sd"),
    ]
    wanted_types = ["ClothingStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name")
        item["branch"] = response.xpath('//div[@class="store-heading"]/h2/text()').get()
        yield item
