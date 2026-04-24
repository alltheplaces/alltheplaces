from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CoachUSSpider(SitemapSpider, StructuredDataSpider):
    name = "coach_us"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    sitemap_urls = ["https://www.coach.com/stores/sitemap.xml"]
    sitemap_rules = [(r"/stores/(outlets/)?\w\w/[-\w]+/.+$", "parse_sd")]
    wanted_types = ["Store", "OutletStore"]
    drop_attributes = {"image"}
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].startswith("COACH Outlet"):
            item["name"] = "COACH Outlet"
        else:
            item["name"] = "COACH"

        item["branch"] = ld_data["name"].removeprefix(item["name"]).strip()

        yield item
