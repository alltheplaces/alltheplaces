from scrapy import Selector, Spider
from scrapy.http import Request

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PnaNAZASpider(Spider):
    name = "pna_na_za"
    allowed_domains = ["pnastores.co.za"]
    start_urls = ["https://pnastores.co.za/store-locator.php"]
    item_attributes = {
        "brand": "PNA",
        "brand_wikidata": "Q126911439",
    }
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    skip_auto_cc_domain = True

    def parse(self, response):
        for province in response.xpath('.//div[contains(@class, "store-list")]'):
            province_name = province.xpath("string(.//h4)").get().strip()
            for link in province.xpath('.//a[contains(@href, "/store/")]/@href').getall():
                yield Request(
                    url="https://pnastores.co.za" + link, callback=self.parse_item, meta={"province": province_name}
                )

    def parse_item(self, response):
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["state"] = response.meta["province"]
        if item["state"] == "Namibia":
            item.pop("state")
        item["branch"] = response.xpath(".//title/text()").get().split("|")[0].replace("PNA", "").strip()
        addr = Selector(
            text=response.text.split("<!-- ngIf: shop.physical_address.place -->")[1].split(
                "<!-- end ngIf: shop.physical_address.place -->"
            )[0]
        )
        addr_text = addr.xpath("string(.//div)").get()
        item["addr_full"] = clean_address(addr_text)
        addr_lines = [line.strip() for line in addr_text.split("\n") if line.strip() != ""]
        item["street_address"] = addr_lines[0]
        try:
            int(addr_lines[-1])
            item["postcode"] = addr_lines[-1]
            if item["postcode"] == "0000":
                item.pop("postcode")
        except ValueError:
            pass

        item["email"] = response.xpath('.//a[contains(@href, "mailto:")]/@href').get()
        item["phone"] = response.xpath('.//a[contains(@href, "tel:")]/@href').get()

        item["opening_hours"] = OpeningHours()
        hours = Selector(
            text=response.text.split("<!-- ngIf: shop.trading_hours.monday -->")[1].split(
                "<!-- end ngIf: shop.trading_hours.monday -->"
            )[0]
        )
        item["opening_hours"].add_ranges_from_string(hours.xpath("string(.//div)").get())

        yield item
