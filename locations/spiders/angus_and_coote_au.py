from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AngusAndCooteAUSpider(SitemapSpider, StructuredDataSpider):
    name = "angus_and_coote_au"
    item_attributes = {"brand": "Angus & Coote", "brand_wikidata": "Q18162112"}
    allowed_domains = ["www.anguscoote.com.au"]
    sitemap_urls = ["https://www.anguscoote.com.au/content/sitemaps/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]
    time_format = "%I:%M%p"

    def post_process_item(self, item, location, ld_data):
        item["website"] = item["ref"]
        item.pop("facebook")
        item.pop("image")
        yield item
