from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import Request

from locations.hours import DAYS_EN, DAYS_PT, DELIMITERS_EN, DELIMITERS_PT, OpeningHours
from locations.items import Feature, merge_items
from locations.spiders.nedbank_za import NEDBANK_SHARED_ATTRIBUTES


class NedbankMZSpider(Spider):
    name = "nedbank_mz"
    item_attributes = NEDBANK_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.nedbank.co.mz/en/customer-support/branches.aspx",
        "https://www.nedbank.co.mz/apoio-ao-cliente/rede-de-balc%C3%B5es.aspx",
    ]
    saved_items = {"en": {}, "pt": {}}
    languages_finished = 0

    def parse(self, response):
        for location in response.xpath('.//div[@class="balcao_morada"]'):
            item = Feature()

            item["branch"] = location.xpath('.//span[@class="titulo"][contains(@onclick, "javascript")]/text()').get()

            item["lat"] = (
                location.xpath('.//span[@class="titulo"][contains(@onclick, "javascript")]/@onclick')
                .get()
                .split("replaceCustom('")[1]
                .rstrip("'),; ")
                .replace(",", ".")
            )
            item["lon"] = (
                location.xpath('.//span[@class="titulo"][contains(@onclick, "javascript")]/@onclick')
                .get()
                .split("replaceCustom('")[2]
                .rstrip("'),; ")
                .replace(",", ".")
            )

            item["street_address"] = location.xpath('.//span[contains(@id, "dtContacto_Labmorada")]/text()').get()
            item["city"] = location.xpath('.//span[contains(@id, "dtContacto_Labcidade")]/text()').get()

            phone = location.xpath('.//span[contains(@id, "dtContacto_Labtelefone")]/text()').get()
            clean_phone = phone.lower().replace("tel:", "").strip().replace("+ 258", "+258")
            if "/" in clean_phone:
                phones = clean_phone.split("/")
                if max([len(ext) for ext in phones[1:]]) < 3:
                    root = phones[0]
                    item["phone"] = root
                    for ext in phones[1:]:
                        item["phone"] += "; " + root[: -len(ext)] + ext
                else:
                    item["phone"] = "; ".join(phones)
            else:
                item["phone"] = clean_phone

            if "/en/" in response.url:
                days = DAYS_EN
                delimiters = DELIMITERS_EN
            else:
                days = DAYS_PT
                delimiters = DELIMITERS_PT
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                location.xpath('.//span[contains(@id, "dtContacto_LabhorFuncSegSex")]/text()').get(),
                days=days,
                delimiters=delimiters,
            )
            item["opening_hours"].add_ranges_from_string(
                location.xpath('.//span[contains(@id, "dtContacto_LabhorSabado")]/text()').get(),
                days=days,
                delimiters=delimiters,
            )

            item["ref"] = f"{item["lat"]},{item["lon"]}"

            if "/en/" in response.url:
                self.saved_items["en"][item["ref"]] = item
            else:
                self.saved_items["pt"][item["ref"]] = item

        if event_target := response.xpath('.//a[contains(@id, "ctl05_contact_12_ltnnext")]/@href').get():
            view_state = response.xpath('.//input[@id="__VIEWSTATE"]/@value').get()
            event_target = event_target.removeprefix("javascript:__doPostBack('").removesuffix("','')")
            body = urlencode(
                {
                    "__EVENTTARGET": event_target,
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": view_state,
                    "ctl00$ctl00$ContentPlaceHolderDefault$menu_box_2$txtPesquisa": "",
                    "__VIEWSTATEGENERATOR": "CA0B0334",
                    "__VIEWSTATEENCRYPTED": "",
                }
            )
            yield Request(
                url=response.url,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=body,
            )
        else:
            self.languages_finished += 1
            if self.languages_finished == 2:
                yield from merge_items(self.saved_items, "pt")
