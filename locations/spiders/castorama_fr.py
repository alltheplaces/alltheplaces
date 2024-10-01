from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class CastoramaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "castorama_fr"
    item_attributes = {"brand": "Castorama", "brand_wikidata": "Q966971"}
    sitemap_urls = ["https://www.castorama.fr/static/sitemap.xml"]
    sitemap_rules = [(r"/store/\d+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        for opening_hour in ld_data["openingHoursSpecification"]:
            if "opens" in opening_hour:
                oh.add_range(
                    DAYS_EN[opening_hour["dayOfWeek"]],
                    opening_hour["opens"][0:5],
                    opening_hour["closes"][0:5],
                )
                item["opening_hours"] = oh
        yield item
    drop_attributes = {"image"}
