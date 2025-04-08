import html

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LappartFitnessFRSpider(SitemapSpider, StructuredDataSpider):
    name = "lappart_fitness_fr"
    item_attributes = {"brand": "L'Appart Fitness", "brand_wikidata": "Q120734255"}
    sitemap_urls = ["https://clubs.lappartfitness.com/locationsitemap1.xml"]
    sitemap_rules = [("https://clubs.lappartfitness.com/.*", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = html.unescape(item.pop("name")).removeprefix("L'Appart Fitness ")

        apply_category(Categories.GYM, item)

        yield item
