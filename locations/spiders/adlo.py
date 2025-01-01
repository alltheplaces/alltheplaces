from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, PaymentMethods, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class AdloSpider(CrawlSpider):
    name = "adlo"
    allowed_domains = ["www.adlo-securitydoors.com"]
    start_urls = ["https://www.adlo-securitydoors.com/en/shops/list"]
    item_attributes = {"brand": "ADLO", "brand_wikidata": "Q116862985", "extras": Categories.SHOP_DOORS.value}

    # split the page into separate countries
    rules = (
        Rule(
            LinkExtractor(allow=r"en/shops/.+", restrict_xpaths="//div[@class='bl' and contains(.,'Slovak')]"),
            follow=True,
            callback="parse_item",
            cb_kwargs={"country": "SK"},
        ),
        Rule(
            LinkExtractor(allow=r"en/shops/.+", restrict_xpaths="//div[@class='bl' and contains(.,'Deutschland')]"),
            follow=True,
            callback="parse_item",
            cb_kwargs={"country": "DE"},
        ),
        Rule(
            LinkExtractor(
                allow=r"en/shops/.+",
                restrict_xpaths="//div[@class='bl' and (contains(.,'Switzerland') or contains(.,'Schweiz'))]",
            ),
            follow=True,
            callback="parse_item",
            cb_kwargs={"country": "CH"},
        ),
        Rule(
            LinkExtractor(allow=r"en/shops/.+", restrict_xpaths="//div[@class='bl' and contains(.,'Austria')]"),
            follow=True,
            callback="parse_item",
            cb_kwargs={"country": "AT"},
        ),
        Rule(
            LinkExtractor(allow=r"en/shops/.+", restrict_xpaths="//div[@class='bl' and contains(.,'Denmark')]"),
            follow=True,
            callback="parse_item",
            cb_kwargs={"country": "DK"},
        ),
        Rule(
            LinkExtractor(allow=r"en/shops/.+", restrict_xpaths="//div[@class='bl' and contains(.,'Czech')]"),
            follow=True,
            callback="parse_item",
            cb_kwargs={"country": "CZ"},
        ),
    )

    def _build_request(self, rule_index, link):
        # set cookie consent to allow Google Maps iframe
        return Request(
            url=link.url,
            callback=self._callback,
            errback=self._errback,
            meta=dict(rule=rule_index, link_text=link.text),
            cookies=dict(cookies_setting="1111"),
        )

    def parse_item(self, response, country):
        item = Feature()
        item["ref"] = response.url.strip("%20").split("/")[-1]
        web = response.xpath("//div[contains(., 'Web:')]/a/text()[normalize-space()]").get()
        if web is not None:
            if not web.startswith("http"):
                web = "https://" + web
            item["website"] = web
        item["name"] = response.xpath("//div[@class='predajna']/h1/text()[normalize-space()]").get()
        item["street_address"] = response.xpath("//div[contains(., 'Address:')]/text()[normalize-space()]").get()
        item["country"] = country
        extract_google_position(item, response)
        extract_phone(item, response)
        card = response.xpath("//div[contains(., 'Card payment:')]/text()[normalize-space()]").get()
        if card is not None:
            card_accepted = card.strip()
            if card_accepted == "yes" or card_accepted == "no":
                apply_yes_no(PaymentMethods.DEBIT_CARDS, item, card_accepted == "yes", False)
                apply_yes_no(PaymentMethods.CREDIT_CARDS, item, card_accepted == "yes", False)
        return item
