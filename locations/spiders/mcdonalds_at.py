from typing import Any

import scrapy
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import CLOSED_DE, DAYS_DE, OpeningHours
from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsATSpider(SitemapSpider):
    name = "mcdonalds_at"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.at"]
    sitemap_urls = ["https://www.mcdonalds.at/wso_restaurant-sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["lat"] = response.xpath("//@data-marker-icon-lat").get()
        item["lon"] = response.xpath("//@data-marker-icon-lng").get()
        item["addr_full"] = response.xpath('//meta[@property="og:title"]/@content').get().removesuffix(" - McDonald’s")

        services = response.xpath('//*[@class="wso-tax-img"]/img/@alt').getall()

        apply_yes_no(Extras.WIFI, item, "Wlan Icon" in services)

        if "McCafe Icon" in services:
            mccafe = item.deepcopy()
            mccafe["ref"] = "{}-mccafe".format(item["ref"])
            mccafe["brand"] = "McCafé"
            mccafe["brand_wikidata"] = "Q3114287"
            apply_category(Categories.CAFE, mccafe)
            yield mccafe

        oh = OpeningHours()

        selector = scrapy.Selector(text=response.xpath('//div[@id="restaurants"]').get())

        for p in selector.xpath(".//p[string-length(text()) > 0]"):
            if day := p.xpath("./span/text()").get():
                day = day.title()
                if day := DAYS_DE.get(day):
                    open, close = (p.xpath("text()[1]").get()).split(" - ")
                    oh.add_range(day, open, close, closed=CLOSED_DE)
        item["opening_hours"] = oh

        apply_yes_no(Extras.DELIVERY, item, "McDelivery Icon" in services)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "McDrive Icon" in services)

        apply_category(Categories.FAST_FOOD, item)

        yield item
