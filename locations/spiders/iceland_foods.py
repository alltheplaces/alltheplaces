from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class IcelandFoodsSpider(SitemapSpider, StructuredDataSpider):
    name = "iceland_foods"
    item_attributes = {"brand": "Iceland", "brand_wikidata": "Q721810"}
    allowed_domains = ["www.iceland.co.uk"]
    sitemap_urls = ["https://www.iceland.co.uk/sitemap-store-site-map.xml"]
    sitemap_rules = [
        (
            r"https://www\.iceland\.co\.uk/store-finder/store\?StoreID=(\d+)&StoreName=",
            "parse_sd",
        )
    ]
    wanted_types = ["LocalBusiness"]
    search_for_phone = False
    requires_proxy = True

    def inspect_item(self, item, response):
        item["name"] = response.xpath("/html/head/title/text()").get()

        if "FWH" in item["name"] or "Food Ware" in item["name"]:
            # The Food Warehouse, obtained via its own spider
            # The name usually ends with FWH or has Food Warehouse, sometime truncated.
            return

        if "IRELAND" in item["name"]:
            item["country"] = "IE"
        else:
            item["country"] = "GB"

        if phone := response.xpath('//div[@class="phone"]/text()').get():
            item["phone"] = phone.strip()

        yield item
