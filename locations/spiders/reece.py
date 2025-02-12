from scrapy import Selector
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class ReeceSpider(SitemapSpider, StructuredDataSpider):
    name = "reece"
    item_attributes = {"brand_wikidata": "Q29025524"}
    allowed_domains = [
        "www.reece.com.au",
        "www.reece.co.nz",
    ]
    sitemap_urls = [
        "https://www.reece.com.au/sitemaps/store_sitemap.xml",
        "https://www.reece.co.nz/sitemaps/store_sitemap.xml",
    ]
    wanted_types = ["Organization"]

    def post_process_item(self, item, response, ld_data):
        item["ref"] = response.xpath("//input/@data-brcode").get()
        item["name"] = response.xpath("//input/@data-bname").get()
        item["brand"] = Selector(text=response.xpath("//input/@data-cname").get()).xpath("//text()").get()
        item["lat"] = response.xpath("//input/@data-lat").get()
        item["lon"] = response.xpath("//input/@data-lon").get()
        if "www.reece.co.nz" in response.url:
            item.pop("state")
        if response.xpath("//input/@data-phone"):
            item["phone"] = response.xpath("//input/@data-phone").get()
        item["website"] = response.url
        item.pop("image")

        apply_category(Categories.SHOP_TRADE, item)
        match item["brand"]:
            case "Reece Actrol" | "Reece HVAC-R":
                apply_category(Categories.TRADE_HVAC, item)
            case "Reece Bathroom Life" | "Reece NZ Bathroom Life":
                apply_category(Categories.TRADE_BATHROOM, item)
            case "Reece Civil" | "Reece Onsite" | "Reece Plumbing Centre" | "Reece Viadux":
                apply_category(Categories.TRADE_PLUMBING, item)
            case "Reece Fire":
                apply_category(Categories.TRADE_FIRE_PROTECTION, item)
            case "Reece Irrigation & Pools":
                apply_category(Categories.TRADE_IRRIGATION, item)
                apply_category(Categories.TRADE_SWIMMING_POOL_SUPPLIES, item)
            case "Reece Pipeline Supplies Aust":
                apply_category(Categories.TRADE_FIRE_PROTECTION, item)
                apply_category(Categories.TRADE_HVAC, item)
                apply_category(Categories.TRADE_PLUMBING, item)

        item["opening_hours"] = OpeningHours()
        hours_string = " ".join(response.xpath('//tr[contains(@class, "branch-hours")]/td/text()').getall())
        item["opening_hours"].add_ranges_from_string(hours_string)

        yield item
