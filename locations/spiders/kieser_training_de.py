from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KieserTrainingDESpider(SitemapSpider, StructuredDataSpider):
    name = "kieser_training_de"
    item_attributes = {"brand": "Kieser Training", "brand_wikidata": "Q1112367"}
    wanted_types = ["ExerciseGym"]
    sitemap_urls = ["https://www.kieser-training.de/sitemap.xml"]
    sitemap_follow = ["studios"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["openingHoursSpecification"] = None
