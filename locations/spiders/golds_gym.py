from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoldsGymSpider(SitemapSpider, StructuredDataSpider):
    name = "golds_gym"
    item_attributes = {"brand": "Gold's Gym", "brand_wikidata": "Q1536234"}
    sitemap_urls = ["https://www.goldsgym.com/gym_index-sitemap.xml"]
    wanted_types = ["ExerciseGym"]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("sitemap_index.xml", "")
            yield entry
