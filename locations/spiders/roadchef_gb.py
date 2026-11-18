from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class RoadchefGBSpider(SitemapSpider, StructuredDataSpider):
    name = "roadchef_gb"
    item_attributes = {"operator": "Roadchef", "operator_wikidata": "Q7339582"}
    sitemap_urls = ["https://roadchef.com/sitemap.xml"]
    sitemap_rules = [(r"https://roadchef.com/motorway-services/[-\w]+", "parse")]
    wanted_types = ["LocalBusiness"]
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rstrip("/").split("/")[-1]
        item["website"] = response.url
        item["street_address"] = None
        item["city"] = (item.get("city") or "").strip() or None
        item["postcode"] = (item.get("postcode") or "").strip() or None
        apply_category(Categories.HIGHWAY_SERVICES, item)
        yield item
