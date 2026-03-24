import re
from typing import Any, Iterable

from chompjs import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class RelaisAndChateauxSpider(SitemapSpider):
    name = "relais_and_chateaux"
    item_attributes = {"brand": "Relais & Châteaux", "brand_wikidata": "Q1432809"}
    sitemap_urls = ["https://www.relaischateaux.com/us/rc-sitemap.xml"]
    sitemap_rules = [("/hotel/", "parse")]

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            # fix invalid urls e.g. wwww.
            entry["loc"] = re.sub(r"https://[w]+\.(.+)", r"https://www.\1", entry["loc"])
            yield entry

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(response.xpath('//script[@type="application/json"]/text()').get())["props"][
            "pageProps"
        ]["data"].pop("tab_generic_informations")
        data.update(data.pop("localisation"))
        item = DictParser.parse(data)
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([item.pop("addr_full", ""), data["address2"], data["address3"]])
        item["website"] = item["extras"]["website:en"] = response.url
        item["extras"]["website:fr"] = response.xpath('//link[@rel="alternate"][@hreflang="fr-fr"]/@href').get()
        item["extras"]["website:de"] = response.xpath('//link[@rel="alternate"][@hreflang="de-de"]/@href').get()
        item["extras"]["website:es"] = response.xpath('//link[@rel="alternate"][@hreflang="es-es"]/@href').get()
        item["extras"]["website:it"] = response.xpath('//link[@rel="alternate"][@hreflang="it-it"]/@href').get()
        apply_category(Categories.HOTEL, item)
        yield item
