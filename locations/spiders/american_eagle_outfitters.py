from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AmericanEagleOutfittersSpider(SitemapSpider, StructuredDataSpider):
    name = "american_eagle_outfitters"
    item_attributes = {"brand": "American Eagle Outfitters", "brand_wikidata": "Q2842931"}
    sitemap_urls = ["https://stores.aeostores.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["brand"] = response.xpath('//*[@class="LocationName-brand"]/text()').get()
        yield item
