from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider, clean_facebook
from locations.categories import Categories, apply_category


class DessangeSpider(SitemapSpider, StructuredDataSpider):
    name = "dessange"
    item_attributes = {
        "brand": "Dessange",
        "brand_wikidata": "Q62979914",
    }
    sitemap_urls = ["https://salon.dessange.com/sitemap.xml"]
    sitemap_rules = [
        (r"fr/salon-coiffure/", "parse_sd"),
    ]
    time_format = '%H%M'
    drop_attributes = ["image", "twitter"]

    #website return 404 errors when spidering faster
    custom_settings = {"DOWNLOAD_DELAY" : 2.5}

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_HAIRDRESSER, item)
        item["branch"] = (item.pop("name") or "").removeprefix("DESSANGE ")
        
        cleaned_facebook = clean_facebook(item.get("facebook"))
        if cleaned_facebook in ["https://www.facebook.com/DESSANGE.Paris/", "https://www.facebook.com/DESSANGE.Paris" ]:
            item["facebook"] = None

        yield item
