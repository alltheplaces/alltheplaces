from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BAndMGBSpider(SitemapSpider, StructuredDataSpider):
    name = "b_and_m_gb"
    item_attributes = {"brand": "B&M", "brand_wikidata": "Q4836931", "country": "GB"}
    allowed_domains = ["www.bmstores.co.uk"]
    sitemap_urls = ["https://www.bmstores.co.uk/hpcstores/storessitemap"]
    sitemap_rules = [(r"/stores/[^/]+-(\d+)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        item["name"] = response.xpath('//span[@class="bm-line-compact"]/text()').get()

        yield item
