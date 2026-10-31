import re
from typing import Any
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature


class LeKiosqueAPizzasFRSpider(SitemapSpider):
    name = "le_kiosque_a_pizzas_fr"
    item_attributes = {"brand": "Le Kiosque à Pizzas", "brand_wikidata": "Q3223839"}
    allowed_domains = ["www.le-kiosque-a-pizzas.com"]
    sitemap_urls = ["https://www.le-kiosque-a-pizzas.com/sitemap.xml"]
    sitemap_rules = [(r"/fiche-[^/]+--\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        address = response.xpath('//address/a[contains(@href, "maps.google.com")]')
        if not address:
            # Closed kiosks redirect to the home page
            return

        item = Feature()
        item["ref"] = response.url.rsplit("--", 1)[-1]
        item["website"] = response.url
        item["branch"] = self.parse_branch(response.xpath("normalize-space(//title)").get(""), address.attrib["href"])
        if coords := re.search(r"ll=(-?[\d.]+),(-?[\d.]+)", address.attrib["href"]):
            item["lat"], item["lon"] = coords.groups()
        lines = [line.strip() for line in address.xpath("./text()").getall() if line.strip()]
        item["street_address"] = lines[0] if len(lines) > 1 else None
        # A few postcodes have a space in them, e.g. "37 230 FONDETTES"
        if postcode_city := re.match(r"(\d{2})\s?(\d{3})\s+(.+)", lines[-1]):
            item["postcode"] = postcode_city.group(1) + postcode_city.group(2)
            item["city"] = postcode_city.group(3)
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').get("") or None
        item["opening_hours"] = self.parse_hours(response)
        yield item

    @staticmethod
    def parse_branch(title: str, map_url: str) -> str:
        # Titles are either "Kiosque A Pizzas - Pizzeria à Commentry" or "Le kiosque de FORBACH - Le Kiosque à Pizzas"
        if " - Pizzeria " in title:
            place = title.split(" - Pizzeria ", 1)[1]
            # "au Bugue" is "Le Bugue" and "aux Herbiers" is "Les Herbiers"
            place = re.sub(r"^aux ", "Les ", re.sub(r"^au ", "Le ", place))
            return re.sub(r"^(?:à |en )", "", place)
        if m := re.match(r"Le kiosque de (.+) - Le Kiosque à Pizzas$", title):
            return m.group(1)
        # Otherwise use the map link, e.g. "q=Le kiosque à pizzas COMMENTRY&ll=..."
        query = unquote(map_url.split("q=", 1)[-1].split("&", 1)[0])
        return re.sub(r"(?i)^le kiosque à pizzas\s+", "", query)

    @staticmethod
    def parse_hours(response: Response) -> OpeningHours:
        # e.g. "Lundi: 11h00-13h30 / 17h30-21h00", "Mardi: Fermé le midi / 18h00-21h30", "Mercredi: Fermé / "
        oh = OpeningHours()
        for row in response.xpath("//dl/div[dt and dd]"):
            day = DAYS_FR.get(row.xpath("normalize-space(dt)").get())
            if not day:
                continue  # "Jours fériés"
            times = re.findall(r"(\d{1,2})h(\d{2})\s*-\s*(\d{1,2})h(\d{2})", row.xpath("normalize-space(dd)").get())
            if not times:
                oh.set_closed(day)
            for open_h, open_m, close_h, close_m in times:
                oh.add_range(day, f"{open_h}:{open_m}", f"{close_h}:{close_m}")
        return oh
