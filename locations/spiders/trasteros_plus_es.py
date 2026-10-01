import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TrasterosPlusESSpider(SitemapSpider):
    name = "trasteros_plus_es"
    item_attributes = {"brand": "Trasteros Plus"}
    sitemap_urls = ["https://www.trasterosplus.es/page-sitemap.xml"]
    sitemap_rules = [(r"/alquiler-trasteros(-almeria)?/[^/]+/$", "parse")]

    def parse(self, response):
        if not response.xpath('//h2[contains(., "Detalles de la tienda")]'):
            return
        details = response.xpath(
            '//h2[contains(., "Detalles de la tienda")]/following::div[contains(@class, "wp-block-columns")][1]'
        )
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["addr_full"] = details.xpath('.//strong[text()="Dirección"]/following::a[1]//text()').get()
        if not item["addr_full"]:
            return
        item["branch"] = (
            response.css("h1.titulo-ubicacion::text").get().removeprefix("Alquiler de trasteros en ").split(",")[0]
        )
        item["phone"] = details.xpath('.//a[starts-with(@href, "tel:")]/@href').get()
        if item["phone"] and re.sub(r"\D", "", item["phone"]).endswith("951830110"):
            item["phone"] = None
        item["email"] = details.xpath('.//a[starts-with(@href, "mailto:")]/text()').get()
        if iframe := response.xpath('//iframe/@data-src-cmplz[contains(., "google.com/maps/embed")]').get():
            item["lat"], item["lon"] = url_to_coords(iframe)

        hours_text = " ".join(
            details.xpath('.//strong[text()="Horario de acceso"]/following::span[1]//text()').getall()
        )
        if m := re.search(r"(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})", hours_text):
            item["opening_hours"] = oh = OpeningHours()
            oh.add_days_range(DAYS, m.group(1), m.group(2))

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
