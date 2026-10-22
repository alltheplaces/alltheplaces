import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EosFitnessUSSpider(SitemapSpider, StructuredDataSpider):
    name = "eos_fitness_us"
    item_attributes = {"brand": "EōS Fitness", "brand_wikidata": "Q127770873"}
    sitemap_urls = ["https://www.eosfitness.com/robots.txt"]
    sitemap_rules = [("/gym/", "parse")]
    wanted_types = ["ExerciseGym"]
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "Coming Soon" in response.xpath("//head/title/text()").get(""):
            return
        apply_category(Categories.GYM, item)

        hours = " ".join(
            response.xpath(
                "//p[normalize-space()='EōS FITNESS HOURS' or normalize-space()='HOURS']/following-sibling::p[1]//text()"
            ).getall()
        )
        item["opening_hours"] = OpeningHours()
        if "24/7" in hours:
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
        else:
            hours = re.sub(r"(?:Open )?24 Hours", "12AM - 11:59PM", hours)
            hours = re.sub(r"Opens at (\S+)", r"\1 - 11:59PM", hours)
            hours = re.sub(r"Closes at (\S+)", r"12AM - \1", hours)
            item["opening_hours"].add_ranges_from_string(hours)
        yield item
