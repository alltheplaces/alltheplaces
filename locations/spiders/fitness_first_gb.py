from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class FitnessFirstGBSpider(SitemapSpider, StructuredDataSpider):
    name = "fitness_first_gb"
    item_attributes = {"brand": "Fitness First", "brand_wikidata": "Q127120"}
    sitemap_urls = ["https://www.fitnessfirst.co.uk/xml-sitemap"]
    sitemap_rules = [("/find-a-gym/([^/]+)$", "parse_sd")]
    wanted_types = ["ExerciseGym"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = response.url
        extract_google_position(item, response)
        yield item
