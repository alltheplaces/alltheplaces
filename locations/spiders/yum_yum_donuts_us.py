from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class YumYumDonutsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "yum_yum_donuts_us"
    item_attributes = {
        "brand": "Yum Yum Donuts",
        "brand_wikidata": "Q8061011",
        "name": "Yum Yum Donuts",
    }
    sitemap_urls = ["https://locations.yumyumdonuts.com/sitemap.xml"]
    sitemap_rules = [(r"/california/[^/]+/\d+-[^/]+/$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        if not item.get("opening_hours"):
            rules = ld_data["openingHoursSpecification"]
            if len(rules) == 7 and all(rule["opens"] == rule["closes"] == "00:00:00" for rule in rules):
                oh = OpeningHours()
                oh.add_days_range(DAYS, "00:00", "23:59")
                item["opening_hours"] = oh
        apply_category(Categories.FAST_FOOD, item)
        yield item
