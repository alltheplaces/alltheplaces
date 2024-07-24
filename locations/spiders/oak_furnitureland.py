from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class OakFurniturelandSpider(SitemapSpider):
    name = "oak_furnitureland"
    item_attributes = {
        "brand": "Oak Furnitureland",
        "brand_wikidata": "Q16959724",
        "country": "GB",
    }
    sitemap_urls = ["https://www.oakfurnitureland.co.uk/sitemaps/sitemap.xml"]
    sitemap_rules = [("/page/", "parse")]

    def parse(self, response):
        if "PERMANENTLY CLOSED" in "".join(response.xpath('//div[@id="title"]/descendant::*/text()').getall()):
            return

        if item := LinkedDataParser.parse(response, "LocalBusiness"):
            item["ref"] = response.url
            return item
