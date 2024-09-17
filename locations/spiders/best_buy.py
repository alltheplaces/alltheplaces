from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class BestBuySpider(SitemapSpider, StructuredDataSpider):
    name = "best_buy"
    item_attributes = {"brand_wikidata": "Q533415", "extras": Categories.SHOP_ELECTRONICS.value}
    allowed_domains = ["stores.bestbuy.com"]
    sitemap_urls = ["https://stores.bestbuy.com/sitemap.xml"]
    sitemap_rules = [(r"/[a-z]{2}/[\w-]+/[\w-]+.html", "parse_sd")]
    search_for_image = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = response.xpath('//span[@class="LocationName-geo"]/text()').get()
        item["brand"] = item["name"] = response.xpath('//span[@class="LocationName-brand"]/text()').get()
        item["ref"] = response.xpath('//input[@name="extStoreId"]/@value').get()
        yield item
