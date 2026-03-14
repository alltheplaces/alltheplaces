import re
from urllib.parse import parse_qs, urlparse

from scrapy import Request, Selector
from scrapy.spiders import XMLFeedSpider
from scrapy.utils.spider import iterate_spider_output

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_ES, OpeningHours
from locations.items import Feature


class CajamarESSpider(XMLFeedSpider):
    name = "cajamar_es"
    item_attributes = {"brand": "Cajamar", "brand_wikidata": "Q8254971"}
    start_urls = [
        "https://www.grupocooperativocajamar.es/frontend/kml/cajerostodo.kml",
        "https://www.grupocooperativocajamar.es/frontend/kml/oficinastodo.kml",
    ]
    iterator = "xml"
    itertag = "Placemark"

    def parse_nodes(self, response, nodes):
        response.selector.remove_namespaces()
        for node in response.xpath("//Placemark"):
            for item in iterate_spider_output(self.parse_node(response, node)):
                yield item

    def parse_node(self, response, node):
        is_bank = "oficinastodo" in response.url

        description_html = node.xpath("./description/text()").get()
        if not description_html:
            return

        desc = Selector(text=description_html)
        item = Feature(
            lat=node.xpath("./LookAt/latitude/text()").get(),
            lon=node.xpath("./LookAt/longitude/text()").get(),
            website=desc.xpath(".//a/@href").getall()[-1],
        )

        if branch_name := desc.xpath(".//span[@class='negrita']/text()").get():
            if match := re.match(r"[\d.]+\s+(.+)", branch_name):
                item["branch"] = match.group(1).strip()

        # Extract slug from website URL and combine with branch name as ref
        if slug_match := re.search(r"busqueda-(?:oficinas|cajeros)/([^/]+)", item.get("website", "")):
            slug = slug_match.group(1)
            item["ref"] = f"{slug}_{branch_name}" if branch_name else slug

        if is_bank:
            apply_category(Categories.BANK, item)
            if match := re.search(r"</p>([^<]+)<br\s*/?>(\d{5})\s+([^(]+)\(([^)]+)\)", description_html):
                item["street_address"], item["postcode"], item["city"], item["state"] = [
                    g.strip() for g in match.groups()
                ]
            item["opening_hours"] = self.parse_hours(desc.xpath(".//small[b]/text()").get())
            yield Request(url=item["website"], callback=self.parse_detail, meta={"item": item})
        else:
            apply_category(Categories.ATM, item)
            if match := re.search(r"</b></p>([^<]+)<br\s*/?>([^<]+)\(([^)]+)\)", description_html):
                item["street_address"], item["city"], item["state"] = [g.strip() for g in match.groups()]
            if link := desc.xpath(".//a[contains(@href, 'operaciones-y-funciones')]/@href").get():
                params = parse_qs(urlparse(link).query)
                apply_yes_no(PaymentMethods.CONTACTLESS, item, "1" in params.get("contactless", []))
                apply_yes_no(Extras.CASH_IN, item, "1" in params.get("bna", []))
            yield item

    def parse_detail(self, response):
        item = response.meta["item"]
        item["phone"] = response.xpath("//a[starts-with(@href, 'tel:')]/text()").get()
        yield item

    def parse_hours(self, text: str) -> OpeningHours | None:
        if not text:
            return None
        oh = OpeningHours()
        if match := re.search(r"De\s+(\w+)\s+a\s+(\w+)\s+de\s+([\d.:]+)\s+a\s+([\d.:]+)", text):
            start_day, end_day = DAYS_ES.get(match.group(1).capitalize()), DAYS_ES.get(match.group(2).capitalize())
            if start_day and end_day:
                oh.add_days_range(
                    DAYS[DAYS.index(start_day) : DAYS.index(end_day) + 1],
                    match.group(3).replace(".", ":"),
                    match.group(4).replace(".", ":"),
                )
        return oh or None
