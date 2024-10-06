import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HornbachDESpider(SitemapSpider, StructuredDataSpider):
    name = "hornbach_de"
    item_attributes = {"brand": "HORNBACH", "brand_wikidata": "Q685926"}
    sitemap_urls = ["https://www.hornbach.de/robots.txt"]
    sitemap_follow = ["mein-markt"]
    sitemap_rules = [(r"/mein-markt/baumarkt-hornbach-([^/]+)/$", "parse_sd")]
    custom_settings = {"DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"}}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("HORNBACH ")
        open_times_data = response.xpath("//cms-market-info-box/@open-times").get()
        opening_hours = OpeningHours()
        for rule in json.loads(open_times_data)["openTimes"]:
            opening_hours.add_ranges_from_string(":".join([rule["day"].replace(".", ""), rule["time"]]), days=DAYS_DE)
        item["opening_hours"] = opening_hours
        yield item
