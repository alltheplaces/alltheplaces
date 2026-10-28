from typing import Any, Iterable

from chompjs import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


class CamilleAlbaneSpider(SitemapSpider):
    name = "camille_albane"
    item_attributes = {"brand": "Camille Albane", "brand_wikidata": "Q62965183", "name": "Camille Albane"}
    allowed_domains = ["salon.camillealbane.com"]
    sitemap_urls = ["https://salon.camillealbane.com/sitemap.xml"]
    sitemap_rules = [(r"/fr/salon-coiffure/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        salon = self.find_salon(dict(parse_rsc(rsc.encode())), response.url.split("/")[-1])
        if salon is None or salon.get("status") != "published":
            return

        item = DictParser.parse(salon)
        item["ref"] = salon["id"]
        name = item.pop("name") or ""
        if name.upper().startswith("CAMILLE ALBANE "):
            name = name[len("CAMILLE ALBANE ") :]
        item["branch"] = name or None
        item["street_address"] = (item.pop("addr_full") or "").replace("\\'", "'")
        item["website"] = response.url
        item["twitter"] = None
        item["extras"]["ref:partoo"] = salon.get("id_partoo")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            opens = salon.get("{}_morning".format(day.lower()))
            closes = salon.get("{}_night".format(day.lower()))
            if not opens or not closes or opens == "0" or closes == "0":
                item["opening_hours"].set_closed(day)
                continue
            item["opening_hours"].add_range(day, opens.zfill(4), closes.zfill(4), "%H%M")

        apply_category(Categories.SHOP_HAIRDRESSER, item)
        yield item

    def find_salon(self, node: Any, slug: str) -> dict | None:
        if isinstance(node, dict):
            if node.get("slug") == slug and "latitude" in node:
                return node
            children = node.values()
        elif isinstance(node, list):
            children = node
        else:
            return None
        for child in children:
            if salon := self.find_salon(child, slug):
                return salon
        return None
