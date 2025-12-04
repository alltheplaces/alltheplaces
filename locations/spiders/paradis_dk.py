from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class ParadisDKSpider(SitemapSpider):
    name = "paradis_dk"
    item_attributes = {"brand": "Paradis", "brand_wikidata": "Q12330951"}
    sitemap_urls = ["https://paradis-is.dk/isbutik-sitemap.xml"]
    sitemap_follow = ["butikker"]
    sitemap_rules = [(r"/isbutik/[^/]+", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["name"] = (
            response.xpath("//title/text()").get().replace(" – din lokale isbutik med frisklavet is fra Paradis", "")
        )
        item["addr_full"] = response.xpath('//*[@id="main-content"]//p/text()').get()
        item["email"] = (
            response.xpath('//*[@id="main-content"]//*[contains(text(), "Email:")]//text()').get().replace("Email:", "")
        )
        item["phone"] = response.xpath("//*[contains(@href,'tel:')]/text()").get()
        apply_category(Categories.ICE_CREAM, item)

        yield item
