from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class McCoysSpider(SitemapSpider, StructuredDataSpider):
    name = "mccoys"
    item_attributes = {"brand": "McCoy's Building Supply", "brand_wikidata": "Q27877295"}
    allowed_domains = ["www.mccoys.com"]
    sitemap_urls = ["https://www.mccoys.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/[-\w]+", "parse_sd")]
    wanted_types = ["Store"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    time_format = "%I:%M %p"

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["openingHoursSpecification"] = ld_data.pop("OpeningHoursSpecification", None)
