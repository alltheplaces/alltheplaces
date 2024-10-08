from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class SkoringenDKNOSpider(SitemapSpider, StructuredDataSpider):
    name = "skoringen_dk_no"
    item_attributes = {"brand": "Skoringen", "brand_wikidata": "Q12001172"}
    sitemap_urls = ["https://www.skoringen.dk/sitemap.xml", "https://www.skoringen.no/sitemap.xml"]
    sitemap_rules = [(r"/find-butik/.+", "parse_sd"), (r"/finn-butikk/.+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["phone"] = response.xpath('//*[contains(@href, "tel:")]/text()').get()
        item["website"] = item["ref"] = response.url
        apply_category(Categories.SHOP_SHOES, item)
        extract_google_position(item, response)
        item.pop("opening_hours")
        yield item
