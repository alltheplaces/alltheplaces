from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CashConvertersGBSpider(SitemapSpider, StructuredDataSpider):
    name = "cash_converters_gb"
    item_attributes = {"brand": "Cash Converters", "brand_wikidata": "Q5048645"}
    sitemap_urls = ["https://www.cashconverters.co.uk/standard-sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["name"] = None
        item["branch"] = response.xpath("//@data-title").get()

        if "placeholder" in item.get("image", ""):
            item["image"] = None

        yield item
