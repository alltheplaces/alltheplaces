from scrapy.spiders import SitemapSpider

from locations.categories import apply_category
from locations.structured_data_spider import StructuredDataSpider


class ChildcareNetworkUSSpider(SitemapSpider, StructuredDataSpider):
    name = "childcare_network_us"
    sitemap_urls = ["https://schools.childcarenetwork.com/robots.txt"]
    sitemap_rules = [(r"\.com/\w\w/[-\w]+/[-\w]+$", "parse_sd")]
    wanted_types = ["EducationalOrganization"]
    download_delay = 0

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = response.xpath("//h2/text()").get()
        apply_category({"amenity": "kindergarten"}, item)
        yield item
