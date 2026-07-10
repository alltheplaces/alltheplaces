from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class JumeirahSpider(SitemapSpider, StructuredDataSpider):
    name = "jumeirah"
    item_attributes = {"brand": "Jumeirah", "brand_wikidata": "Q1331200"}
    sitemap_urls = ["https://www.jumeirah.com/en/sitemap-en.xml"]
    sitemap_rules = [(r"https://www.jumeirah.com/en/stay/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["addr_full"] = response.xpath('//*[@class="address"]//a//text()').get()
        item["branch"] = item.pop("name").replace("Jumeirah ", "")
        apply_category(Categories.HOTEL, item)
        yield item
