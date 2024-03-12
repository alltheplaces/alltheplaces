from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class ShoppersFoodUSSpider(SitemapSpider, StructuredDataSpider):
    name = "shoppers_food_us"
    item_attributes = {"brand": "Shoppers Food & Pharmacy", "brand_wikidata": "Q7501183"}
    sitemap_urls = ["https://www.shoppersfood.com/content/svu-retail-banners/shoppers/en/stores-sitemap.xml"]
    sitemap_rules = [
        (
            r"\/stores\/view-store\.[\d]+\.html$",
            "parse_sd",
        )
    ]
