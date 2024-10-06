from typing import Iterable

import pycountry
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.volkswagen import VolkswagenSpider


class PorscheHoldingSpider(JSONBlobSpider):
    """
    A spider for car dealerships of Porsche Holding (Volkswagen Group) brands in various countries.
    https://www.porsche-holding.com/en/company/locations
    https://www.porsche-holding.com/en/company/business-divisions/automotive-retail
    """

    name = "porsche_holding"
    brands = {
        "V": VolkswagenSpider.item_attributes,
        # TODO: Apart of Volkswagen API covers some other brands:
        # https://github.com/alltheplaces/alltheplaces/issues/10156#issuecomment-2336428610
        # A for Audi
        # C for Skoda
        # G for group?
        # L for LNF? Not sure what that means
        # P for Porsche
        # S for Seat
    }
    locations_key = "data"
    start_urls = [
        "https://www.porsche-holding.com/en/company/locations",
        "https://www.porsche-holding.com/en/company/locations/asia",
        "https://www.porsche-holding.com/en/company/locations/south-america",
    ]

    base_url = "https://hs.porsche-holding.com/api/v2/dealers"

    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 10,  # API throws 429 very quickly
    }

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield Request(url=url, callback=self.get_countries)

    def get_countries(self, response: Response):
        country_names = response.xpath('//div[@class="porscheholding-countriesViewDropdown__item"]/a/text()').getall()
        self.logger.info(f"Found country names: {country_names}")
        for country_name in country_names:
            matches = pycountry.countries.search_fuzzy(country_name)
            if matches:
                country_code = matches[0].alpha_2
                for brand_slug, brand_info in self.brands.items():
                    url = f"{self.base_url}/{country_code}/{brand_slug}"
                    self.logger.info(f"Fetching brand {brand_slug} for {country_code}")
                    yield Request(
                        url=url,
                        callback=self.check_status,
                        meta={"brand_slug": brand_slug, "brand_info": brand_info, "country": country_code},
                    )
            else:
                self.logger.error(f"Could not find country code for {country_name}")

    def check_status(self, response: Response) -> Iterable[Feature]:
        if response.status != 200:
            self.crawler.stats.inc_value(f"atp/{self.name}/dealers/fail/{response.meta['country']}")
            return
        else:
            yield from self.parse(response)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["bnr"]

        item["brand"] = response.meta["brand_info"].get("brand")
        item["brand_wikidata"] = response.meta["brand_info"].get("brand_wikidata")

        services = feature.get("contracts", {})
        if services.get("sales"):
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, services.get("service"))
        elif services.get("service"):
            apply_category(Categories.SHOP_CAR_REPAIR, item)

        # TODO: other services may be added after more research:
        #       "agent"
        #       "emobility"
        #       "emobilityService"
        #       "naturalGas"
        #       "pluginSales"
        #       "pluginService"
        #       "classicPartsCc"
        #       "accidentSpecialist"
        #       "dwa"
        #       "sbo"
        #       "batteryRepair"
        #       "servicePlus"

        self.parse_hours(item, feature, response.meta["brand_slug"])
        yield item

    def parse_hours(self, item: Feature, feature: dict, brand_slug: str):
        hours = feature.get("openingTimes", [])
        if not hours:
            return
        try:
            for hour in hours:
                oh = OpeningHours()
                # TODO: handle hours better: different hours for different services, where "title" values differ per country
                if hour.get("dwdmContractMatchcodes", "") == brand_slug:
                    for day, times in hour.items():
                        if day in ["title", "dwdmContractMatchcodes"]:
                            continue
                        day = DAYS_EN.get(day.title())
                        if times:
                            for time in times:
                                oh.add_range(day, time.split("-")[0], time.split("-")[1])
                        else:
                            oh.set_closed(day)
                item["opening_hours"] = oh
        except Exception as e:
            self.logger.warning(f"Could not parse hours {hours} for {item['ref']}: {e}")
