from scrapy.spiders import SitemapSpider

from locations.open_graph_spider import OpenGraphSpider


class FantasticSamsCAUSSpider(SitemapSpider, OpenGraphSpider):
    name = "fantastic_sams_ca_us"
    item_attributes = {
        "brand": "Fantastic Sams",
        "brand_wikidata": "Q5434222",
    }
    sitemap_urls = ["https://www.fantasticsams.com/sitemap.xml"]
    sitemap_rules = [
        (r"/salons/fantastic-sams-[\w-]+$", "parse"),
    ]
    wanted_types = ["website"]
    drop_attributes = {"name"}

    def post_process_item(self, item, response):
        item["state"] = response.xpath("//meta[@property='og:region']/@content").get().split("-")[1]
        yield item
