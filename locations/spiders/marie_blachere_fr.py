from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MarieBlachereFRSpider(SitemapSpider, StructuredDataSpider):
    name = "marie_blachere_fr"
    item_attributes = {"brand": "Marie Blachère", "brand_wikidata": "Q62082410"}
    sitemap_urls = ["https://boulangeries.marieblachere.com/sitemap_pois.xml"]
    sitemap_rules = [(r"https://boulangeries\.marieblachere\.com/[^/]+/[^/]+/(\d+)/[^/]+/details$", "parse_sd")]
    wanted_types = ["Bakery"]
    drop_attributes = {"image", "email", "facebook"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if response.xpath('//*[contains(text(), "Horaires habituels")][@id!="__NEXT_DATA__"]'):
            # Linked Data contains special opening hours, we want normal opening hours
            # https://github.com/alltheplaces/alltheplaces/issues/17831
            item["opening_hours"] = None

        item["branch"] = item.pop("name").removeprefix("Marie Blachère ")

        apply_category(Categories.SHOP_BAKERY, item)

        yield item
