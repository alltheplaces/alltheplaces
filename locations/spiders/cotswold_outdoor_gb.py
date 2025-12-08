from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CotswoldOutdoorGBSpider(SitemapSpider, StructuredDataSpider):
    name = "cotswold_outdoor_gb"
    item_attributes = {
        "brand": "Cotswold Outdoor",
        "brand_wikidata": "Q5175488",
        "country": "GB",
    }
    sitemap_urls = ["https://www.cotswoldoutdoor.com/sitemap/store-1.xml"]
    sitemap_rules = [(r"https:\/\/www\.cotswoldoutdoor\.com\/stores\/([-\w]+)\.html$", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        for exclude in ["closed", "test"]:
            if exclude in item["name"].lower():
                return

        if item["ref"] == "marketing-samples":
            return

        yield item
