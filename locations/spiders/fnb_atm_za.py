from typing import Any, AsyncIterator

from scrapy import Selector, Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Request, Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.bp import BpSpider
from locations.spiders.caltex import CaltexSpider
from locations.spiders.engen import EngenSpider
from locations.spiders.shell import ShellSpider
from locations.spiders.shoprite_holdings import SHOPRITE_BRANDS
from locations.spiders.spar_bw_mz_na_sz_za import BRANDS as SPAR_BRANDS
from locations.spiders.total_energies import TotalEnergiesSpider
from locations.user_agents import BROWSER_DEFAULT

ZA_PROVINCES = [
    "Eastern Cape",
    "Free State",
    "Gauteng",
    "KwaZulu-Natal",
    "Limpopo",
    "Mpumalanga",
    "North West",
    "Northern Cape",
    "Western Cape",
]


class FnbAtmZASpider(Spider):
    name = "fnb_atm_za"
    item_attributes = {"brand": "FNB", "brand_wikidata": "Q3072956"}
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 5,
        "ROBOTSTXT_OBEY": False,
    }

    LOCATED_IN_MAPPINGS = [
        (["CALTEX"], CaltexSpider.item_attributes),
        (["BP"], BpSpider.brands["bp"]),
        (["ENGEN"], EngenSpider.item_attributes),
        (["SHELL"], ShellSpider.item_attributes),
        (["TOTAL"], TotalEnergiesSpider.BRANDS["tot"]),
        (
            ["SUPERSPAR"],
            {"brand": SPAR_BRANDS["SUPERSPAR"][0], "brand_wikidata": SPAR_BRANDS["SUPERSPAR"][1]["brand_wikidata"]},
        ),
        (
            ["KWIKSPAR"],
            {"brand": SPAR_BRANDS["KWIKSPAR"][0], "brand_wikidata": SPAR_BRANDS["KWIKSPAR"][1]["brand_wikidata"]},
        ),
        (["SPAR"], SPAR_BRANDS["SPAR"][1]),
        (["BOXER"], {"brand": "Boxer", "brand_wikidata": "Q116586275"}),
        (["SHOPRITE"], SHOPRITE_BRANDS["Shoprite"]),
        (["CHECKERS"], SHOPRITE_BRANDS["Checkers"]),
    ]

    async def start(self) -> AsyncIterator[Request]:
        for province in ZA_PROVINCES:
            yield Request(
                url="https://www.fnb.co.za/Controller?nav=locators.ATMLocatorSearch",
                body="nav=locators.ATMLocatorSearch&atmName=" + province,
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                method="POST",
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        onclicks = response.xpath('.//a[@class="link fontTurq searchResult       "]/@onclick').getall()
        links = [onclick.split("(event,'")[1].split("');")[0] for onclick in onclicks]

        for link in links:
            yield Request(url="https://www.fnb.co.za" + link, callback=self.parse_item)

    def parse_item(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        try:
            details = response.xpath('.//p[@class="      "]').getall()
            deposits = Selector(text=details[2]).xpath(".//strong/text()").get().strip()
            # details[0] # address, in multiple <strong>s
            # details[1] # ATM type, not clear what the different types mean though
            # details[2] # Accepts deposits - Yes/No
            properties = {
                "branch": response.xpath(".//h2/text()").get().strip(),
                "addr_full": clean_address(Selector(text=details[0]).xpath(".//strong/text()").getall()),
                "lon": response.xpath('.//p[@class="  fontGrey   linePadding "]/text()').getall()[1].strip(),
                "lat": response.xpath('.//p[@class="  fontGrey    "]/text()').getall()[1].strip(),
                "ref": response.request.url.replace(
                    "https://www.fnb.co.za/Controller?nav=locators.ATMLocatorSearch&atmid=", ""
                ).replace("&details=true", ""),
            }
            apply_category(Categories.ATM, properties)
            apply_yes_no(Extras.CASH_IN, properties, deposits == "Yes", False)

            properties["located_in"], properties["located_in_wikidata"] = extract_located_in(
                properties.get("branch", ""), self.LOCATED_IN_MAPPINGS, self
            )

            yield Feature(**properties)
        except IndexError:
            yield get_retry_request(
                response.request, spider=self, reason="suspected as bot and no desired data served", max_retry_times=3
            )
