from typing import Iterable

from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class ReeceSpider(SitemapSpider):
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
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def start_requests(self) -> Iterable[Request]:
        for url in self.sitemap_urls:
            yield Request(url=url, callback=self.parse_sitemap)

    def parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            request.meta["playwright"] = True
            request.meta["playwright_include_page"] = True
            yield request

    async def parse(self, response: Response) -> Iterable[Feature]:
        page = response.meta["playwright_page"]
        store_details = await page.main_frame.evaluate("() => window.__NUXT__.data[Object.getOwnPropertyNames(window.__NUXT__.data)[0]]")
        await page.close()
        item = DictParser.parse(store_details)
        item["branch"] = item.pop("name", None)
        item["street_address"] = store_details["address"]["address"]
        item["website"] = response.url

        if hours := store_details.get("tradingHours"):
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                open_time = hours.get(day_name.lower() + "OpenTime")
                close_time = hours.get(day_name.lower() + "CloseTime")
                if open_time and close_time:
                    item["opening_hours"].add_range(day_name, open_time, close_time, "%H:%M:%S")
                else:
                    item["opening_hours"].set_closed(day_name)

        apply_category(Categories.SHOP_TRADE, item)
        for business_unit in store_details["businessUnits"]:
            match business_unit["businessUnitTypeLongDescription"]:
                case "Actrol" | "HVAC-R":
                    apply_category(Categories.TRADE_HVAC, item)
                case "Bathroom Life" | "NZ Bathroom Life":
                    apply_category(Categories.TRADE_BATHROOM, item)
                case "Civil" | "Onsite" | "Plumbing Centre" | "Viadux":
                    apply_category(Categories.TRADE_PLUMBING, item)
                case "Fire":
                    apply_category(Categories.TRADE_FIRE_PROTECTION, item)
                case "Intl Quadratics" | "Irrigation & Pools":
                    apply_category(Categories.TRADE_IRRIGATION, item)
                    apply_category(Categories.TRADE_SWIMMING_POOL_SUPPLIES, item)
                case "Pipeline Supplies Aust":
                    apply_category(Categories.TRADE_FIRE_PROTECTION, item)
                    apply_category(Categories.TRADE_HVAC, item)
                    apply_category(Categories.TRADE_PLUMBING, item)
                case _:
                    self.logger.warning("Unknown business unit type: {}".format(business_unit["businessUnitTypeLongDescription"]))

        yield item
