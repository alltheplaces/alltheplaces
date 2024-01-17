import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class SoutheasternRailwayGBSpider(SitemapSpider, StructuredDataSpider):
    name = "southeastern_railway_gb"
    item_attributes = {"operator": "Southeastern", "operator_wikidata": "Q1696490"}
    sitemap_urls = ["https://www.southeasternrailway.co.uk/robots.txt"]
    sitemap_rules = [("/station-information/stations/", "parse")]
    search_for_facebook = False
    search_for_twitter = False
    search_for_email = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        extract_google_position(item, response)

        if m := re.search(r"Station Code:</b> (\w{3})", response.text):
            item["ref"] = item["extras"]["ref:crs"] = m.group(1)

        apply_category(Categories.TRAIN_STATION, item)

        yield item
