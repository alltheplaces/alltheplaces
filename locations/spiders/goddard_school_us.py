from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GoddardSchoolUSSpider(SitemapSpider, StructuredDataSpider):
    name = "goddard_school_us"
    item_attributes = {"brand": "Goddard School", "brand_wikidata": "Q5576260"}
    sitemap_urls = ["https://www.goddardschool.com/sitemap.xml"]
    sitemap_rules = [(r"/schools/[a-z]{2}/[-\w]+/[-\w]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("The Goddard School of ")
        yield item
