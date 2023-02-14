from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_EN, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BingLeeAUSpider(SitemapSpider, StructuredDataSpider):
    name = "bing_lee_au"
    item_attributes = {"brand": "Bing Lee", "brand_wikidata": "Q4914136"}
    sitemap_urls = ["https://www.binglee.com.au/public/sitemap-locations.xml"]
    sitemap_rules = [(r"\/stores\/", "parse_sd")]
    wanted_types = ["ElectronicsStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = (
            " ".join(item["street_address"].split())
            .replace("Click &amp; Collect Hub Only - Please note: this is not a storefront., ", "")
            .replace("&amp;", "&")
            .replace("O&#x27;", "")
            .replace(",,", ",")
            .replace(" ,", ",")
        )
        item.pop("facebook")
        if "bing-lee-logo" in item["image"]:
            item.pop("image")
        oh = OpeningHours()
        for day_range in ld_data["openingHoursSpecification"]:
            for day in day_range["dayOfWeek"]:
                if day in DAYS_EN:
                    open_m, open_s = divmod(int(day_range["opens"]), 60)
                    open_h, open_m = divmod(open_m, 60)
                    close_m, close_s = divmod(int(day_range["closes"]), 60)
                    close_h, close_m = divmod(close_m, 60)
                    oh.add_range(day, f"{open_h}:{open_m}:{open_s}", f"{close_h}:{close_m}:{close_s}", "%H:%M:%S")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
