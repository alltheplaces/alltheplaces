from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GenghisGrillUSSpider(SitemapSpider, StructuredDataSpider):
    name = "genghis_grill_us"
    item_attributes = {
        "brand": "Genghis Grill",
        "brand_wikidata": "Q29470710",
        "extras": {"amenity": "restaurant", "cuisine": "mongolian_grill"},
    }
    sitemap_urls = ["https://locations.genghisgrill.com/robots.txt"]
    sitemap_rules = [(r".html$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["branch"] = response.xpath("//h2/text()").get()

        yield item
