import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LakelandGBSpider(SitemapSpider, StructuredDataSpider):
    name = "lakeland_gb"
    item_attributes = {
        "brand": "Lakeland",
        "brand_wikidata": "Q16256199",
    }
    sitemap_urls = ["https://www.lakeland.co.uk/export/sitemap/retail-outlets.xml"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data):
        # Lakeland uses addressRegion for city (should be addressLocality)
        item["city"] = item.pop("state", None)
        item["branch"] = response.xpath("//h1/text()").get()
        item["ref"] = response.url.split("/")[-1]

        maps_link = response.xpath('//a[contains(@href, "daddr=")]/@href').get("")
        if coords := re.search(r"daddr=([-\d.]+),([-\d.]+)", maps_link):
            item["lat"] = coords.group(1)
            item["lon"] = coords.group(2)
        else:
            # Closed shop
            return

        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
