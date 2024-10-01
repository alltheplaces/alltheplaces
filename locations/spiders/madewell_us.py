from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MadewellUSSpider(SitemapSpider, StructuredDataSpider):
    name = "madewell_us"
    item_attributes = {"brand": "Madewell", "brand_wikidata": "Q64026213"}
    sitemap_urls = ["https://stores.madewell.com/robots.txt"]
    sitemap_rules = [(r"^https://stores\.madewell\.com/\w\w/\w\w/[-.\w]+/[-.'\w]+$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["phone"] = response.xpath('//div[@id="phone-main"]/a/@href').get()

        yield item
    drop_attributes = {"image"}
