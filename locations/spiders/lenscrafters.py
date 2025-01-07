import json

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider

# Possible duplicate locations at
# https://local.lenscrafters.com/la/metairie/3301-veterans-memorial-blvd.html
# https://local.lenscrafters.com/la/metarie/3301-veterans-memorial-blvd.html
# I can't tell if these are separate stores.


class LenscraftersSpider(SitemapSpider, StructuredDataSpider):
    name = "lenscrafters"
    allowed_domains = ["local.lenscrafters.com"]
    item_attributes = {
        "brand": "LensCrafters",
        "brand_wikidata": "Q6523209",
    }
    sitemap_urls = ["https://local.lenscrafters.com/robots.txt"]
    sitemap_rules = [
        # This excludes /eyedoctors/*
        (r"https://local\.lenscrafters\.com/(canada/)?\w{2}/[-\w]+/[-\w]+\.html", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image", None)
        item.pop("twitter", None)
        item.pop("facebook", None)
        item["website"] = response.url
        item["branch"] = response.css(".Hero-title::text").get()

        script = response.css("head script:not([src])::text").get()
        script = script.removeprefix("window.__INITIAL__DATA__ = ")
        data = json.loads(script)
        coords = data["document"]["yextDisplayCoordinate"]
        item["lat"] = coords["latitude"]
        item["lon"] = coords["longitude"]
        item["ref"] = data["document"]["id"]
        apply_category(Categories.SHOP_OPTICIAN, item)

        yield item
