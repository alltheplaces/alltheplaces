from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CousinsSubsUSSpider(SitemapSpider):
    name = "cousins_subs_us"
    item_attributes = {"brand": "Cousins Subs", "brand_wikidata": "Q5178843"}
    sitemap_urls = ["https://www.cousinssubs.com/sitemap.xml"]
    sitemap_rules = [(r"https://www.cousinssubs.com/locations-directory/[^/]+/[^/]+/[^/]+$", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["name"] = self.item_attributes["brand"]
        item["branch"] = response.xpath("//main//h1/text()").get()
        item["addr_full"] = response.xpath(
            '//*[@class="LocationDirectory_location_details_visit_address__w7TcQ"]/text()'
        ).get()
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        apply_category(Categories.FAST_FOOD, item)
        yield item
