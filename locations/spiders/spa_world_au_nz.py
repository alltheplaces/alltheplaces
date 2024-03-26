from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SpawWorldAUNZSpider(SitemapSpider, StructuredDataSpider):
    name = "spa_world_au_nz"
    item_attributes = {
        "brand": "Spa World",
        "brand_wikidata": "Q124003802",
        "extras": {"shop": "swimming_pool"},
    }
    sitemap_urls = [
        "https://www.spaworld.com.au/sitemap/sitemap-index.xml",
        "https://www.spaworld.co.nz/sitemap/sitemap-index.xml",
    ]
    sitemap_rules = [("find-a-showroom/(.*)", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["postcode"] = str(item["postcode"])
        yield item
