import re
from urllib.parse import parse_qs, urlsplit

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.hours import DAYS_CZ, DAYS_SK, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class DracikSpider(CrawlSpider):
    name = "dracik"
    allowed_domains = ["www.dracik.cz", "www.dracik.sk"]
    start_urls = [
        "https://www.dracik.cz/mapa-prodejen/",
        "https://www.dracik.sk/mapa-predajni/",
    ]
    rules = [
        Rule(
            LinkExtractor(tags=("button",), attrs=("data-modal-href",), allow=r"/branches/branchDetailPopup"),
            callback="parse",
        )
    ]
    item_attributes = {"brand": "Dráčik", "brand_wikidata": "Q57653669"}

    def parse(self, response):
        def get_query_param(link, query_param):
            parsed_link = urlsplit(link)
            queries = parse_qs(parsed_link.query)
            return queries.get(query_param, [])

        id = get_query_param(response.url, "branchId")[0]
        country = response.url.split("/")[2].split(".")[-1].upper()
        detail = response.xpath("//*[@id='storeModal']")

        item = Feature()
        item["ref"] = id
        item["name"] = detail.xpath("//h3/text()[normalize-space()]").get().strip()
        extract_phone(item, detail)
        extract_google_position(item, detail)

        # Example:
        #   City Arena
        #   Kollárová 20
        #   917 01 Trnava
        #   City Arena
        addr_lines = detail.xpath(
            "//div[@class='StoreModal-address']/div[@class='StoreModal-text']/p/text()[normalize-space()]"
        ).getall()
        item["street_address"] = addr_lines[1].strip()
        item["postcode"] = re.findall(r"[0-9]{3}\s?[0-9]{2}", addr_lines[2].strip())[0]
        item["city"] = addr_lines[2].replace(item["postcode"], "").strip()
        item["country"] = country

        # Platba kartou: áno
        card_accepted = (
            detail.xpath(
                "//li[span[contains(text(), 'kartou')]]/span[@class='StoreModalDetails-value']/text()[normalize-space()]"
            )
            .get()
            .strip()
        )
        if card_accepted == "ano" or card_accepted == "áno" or card_accepted == "ne":
            apply_yes_no(PaymentMethods.DEBIT_CARDS, item, card_accepted == "ano" or card_accepted == "áno", False)
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, card_accepted == "ano" or card_accepted == "áno", False)

        # Bezbariérový prístup: áno
        wheelchair = (
            detail.xpath(
                "//li[span[contains(text(),'Bezbariérový')]]/span[@class='StoreModalDetails-value']/text()[normalize-space()]"
            )
            .get()
            .strip()
        )
        if wheelchair == "ano" or wheelchair == "áno" or wheelchair == "ne":
            apply_yes_no(Extras.WHEELCHAIR, item, wheelchair == "ano" or wheelchair == "áno", False)

        if "CZ" == country:
            days = DAYS_CZ
        elif "SK" == country:
            days = DAYS_SK

        if days is not None:
            oh = OpeningHours()
            for row in response.xpath("//*[@class='StoreModal-time']//tr"):
                day = row.xpath("th/text()[normalize-space()]").get().strip()
                hrs = row.xpath("td/text()[normalize-space()]").get().strip()
                oh.add_ranges_from_string(day + " " + hrs, days)
            item["opening_hours"] = oh.as_opening_hours()

        apply_category(Categories.SHOP_TOYS, item)

        yield item
