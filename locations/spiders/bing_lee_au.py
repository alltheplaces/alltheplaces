from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BingLeeAUSpider(SitemapSpider, StructuredDataSpider):
    name = "bing_lee_au"
    item_attributes = {"brand": "Bing Lee", "brand_wikidata": "Q4914136"}
    sitemap_urls = ["https://www.binglee.com.au/public/sitemap-locations.xml"]
    sitemap_rules = [(r"\/stores\/", "parse_sd")]
    requires_proxy = True  # DataDome is used

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = (
            " ".join(item["street_address"].split())
            .replace("Click &amp; Collect Hub Only - Please note: this is not a storefront., ", "")
            .replace("&amp;", "&")
            .replace("O&#x27;", "")
            .replace(",,", ",")
            .replace(" ,", ",")
        )
        item.pop("facebook", None)
        if "bing-lee-logo" in item.get("image", ""):
            item.pop("image", None)
        yield item
