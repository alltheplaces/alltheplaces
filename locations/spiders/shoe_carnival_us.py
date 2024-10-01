from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ShoeCarnivalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "shoe_carnival_us"
    item_attributes = {"brand": "Shoe Carnival", "brand_wikidata": "Q7500007"}
    sitemap_urls = ["https://stores.shoecarnival.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/shoe-store-.+-(\d+)\.html$", "parse")]
    wanted_types = ["ShoeStore"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name")
        item["branch"] = response.xpath('//span[@class="loc-name"]/a/text()').get()
        yield item

