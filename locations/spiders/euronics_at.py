from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class EuronicsATSpider(SitemapSpider, StructuredDataSpider):
    name = "euronics_at"
    RED_ZAC = {"brand": "RED ZAC", "brand_wikidata": "Q1375116"}
    item_attributes = RED_ZAC
    sitemap_urls = ["https://www.redzac.at/iconparc_static/seo/Frontend/sitemap_rzat.xml"]
    sitemap_rules = [(r"/info/Home", "parse_sd")]
    requires_proxy = True

    wanted_types = ["PostalAddress"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["address"] = {
            key: ld_data.pop(key) for key in ld_data.copy() if key not in ["name", "email", "telephone"]
        }

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = response.url
        if not item.get("street_address"):
            item["street_address"] = item.pop("city")
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/@content').get()
        item["email"] = item["email"].replace(" redzac.at", "@redzac.at")
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
