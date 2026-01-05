from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature


class FitnessFirstDESpider(SitemapSpider):
    name = "fitness_first_de"
    item_attributes = {"brand": "Fitness First", "brand_wikidata": "Q127120"}
    sitemap_urls = ["https://www.fitnessfirst.de/sitemap.xml"]
    sitemap_rules = [("/clubs/", "parse_gym")]

    def parse_gym(self, response):
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = response.xpath("//p/span/text()").get()
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get()
        for link in response.xpath("//a[contains(@href, 'google')][contains(@href, 'maps')]/@href").getall():
            item["lat"], item["lon"] = link.split("daddr=")[1].split(",")
            apply_category(Categories.GYM, item)
            yield item  # Only items with a location are gym pages, others are city level pages
