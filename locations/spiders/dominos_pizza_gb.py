from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DominiosGB(SitemapSpider, StructuredDataSpider):
    name = "dominos_pizza_gb"
    item_attributes = {
        "brand": "Domino's Pizza",
        "brand_wikidata": "Q839466",
        "country": "GB",
    }
    sitemap_urls = ["https://www.dominos.co.uk/pizza-near-me/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.dominos\.co\.uk\/pizza-near-me\/[-.\w]+\/([-.\w]+)$",
            "parse_sd",
        )
    ]
    wanted_types = ["FastFoodRestaurant"]
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0"
    )
