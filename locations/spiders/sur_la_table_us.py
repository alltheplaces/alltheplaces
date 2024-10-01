from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SurLaTableUSSpider(SitemapSpider, StructuredDataSpider):
    name = "sur_la_table_us"
    item_attributes = {"brand": "Sur La Table", "brand_wikidata": "Q7645220"}
    allowed_domains = ["www.surlatable.com"]
    sitemap_urls = ["https://www.surlatable.com/sitemap-riositemap.xml"]
    sitemap_rules = [(r"/store-\d+\.html$", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data):
        item["name"] = response.xpath('//h2[@class="locator-title"]/text()').get()
        item["email"] = response.xpath('//a[@title="Email"]/@href').get("").replace("mailTo:", "").strip()
        item["ref"] = item.get("email", "").split("@", 1)[0].replace("slt", "")
        yield item
