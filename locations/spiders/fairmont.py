from typing import Any

import xmltodict
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.central_england_cooperative import set_operator


class FairmontSpider(Spider):
    name = "fairmont"
    FAIRMONT = {"brand": "Fairmont", "brand_wikidata": "Q1393345"}
    start_urls = ["https://www.fairmont.com/frhiuploadedfiles/fairmontpropertymap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('/properties/status[@status="Operational"]/region/property'):
            if location.xpath("./guestrooms/text()").get() == "0":
                continue
            item = DictParser.parse(xmltodict.parse(location.get())["property"])

            slug = location.xpath("./url/text()").get()
            item["city"] = location.xpath("./city/text()").get()
            item["state"] = location.xpath("./province/text()").get()
            item["country"] = location.xpath("./country/text()").get()
            item["addr_full"] = location.xpath("./address/text()").get()
            item["website"] = "https://www.fairmont.com{}".format(slug)
            item["extras"]["fax"] = location.xpath("./fax/text()").get()
            item["extras"]["rooms"] = location.xpath("./guestrooms/text()").get()
            item["ref"] = location.xpath("@propid").get()

            for lang, domain in [
                ("de", "https://www.fairmont.de"),
                ("en", "https://www.fairmont.com"),
                ("es", "https://www.fairmont.mx"),
                ("fr", "https://www.fairmont.fr"),
                ("pt", "https://www.fairmont.net.br"),
                ("tr", "https://www.fairmont-tr.com"),
                ("ru", "https://www.fairmont-ru.com"),
                ("ar", "https://www.fairmont.ae"),
                ("cn", "https://www.fairmont.cn"),
                ("jp", "https://www.fairmont.jp"),
                ("ko", "https://www.fairmont.co.kr/"),
            ]:
                item["extras"]["website:{}".format(lang)] = "{}{}".format(domain, slug)

            if item["name"].startswith("Fairmont"):
                item.update(self.FAIRMONT)
            elif item["name"].endswith("A Fairmont Managed Hotel"):
                set_operator(self.FAIRMONT, item)
                item["nsi_id"] = "N/A"

            apply_category(Categories.HOTEL, item)

            yield item
