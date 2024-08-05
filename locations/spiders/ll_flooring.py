from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LLFlooringSpider(SitemapSpider, StructuredDataSpider):
    name = "ll_flooring"
    item_attributes = {"brand": "LL Flooring", "brand_wikidata": "Q6703090"}
    sitemap_urls = ["https://www.llflooring.com/stores/sitemap.xml"]
    sitemap_rules = [(r"\/stores\/\w+\/[\w-]+\/[\w-]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    # def post_process_item(self, item, response, ld_data, **kwargs):
    #     # The street address has whitespace at the end sometimes
    #     item["street_address"] = item["street_address"].strip()
    #     item["branch"] = item.pop("name").removesuffix(" Store Near You")

    #     yield item
