from scrapy import Request, Spider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.settings import ITEM_PIPELINES
from locations.user_agents import BROWSER_DEFAULT


class GovCmaFuelGBSpider(Spider):
    name = "gov_cma_fuel_gb"
    dataset_attributes = {
        "license": "Open Government Licence v3.0",
        "license:website": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        "license:wikidata": "Q99891702",
        "attribution": "required",
        "attribution:name": "Contains public sector information licensed under the Open Government Licence v3.0.",
    }
    start_urls = ["https://www.gov.uk/guidance/access-fuel-price-data"]
    custom_settings = {
        "ITEM_PIPELINES": ITEM_PIPELINES  # Disable NSI due to mismatch on Tesco Cafe
        | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None},
        "ROBOTSTXT_OBEY": False,  # Asda, Shell!
    }

    user_agent = BROWSER_DEFAULT  # TESCO!

    brand_map = {
        "ASDA": {"brand": "Asda", "brand_wikidata": "Q297410"},
        "Applegreen": {"brand": "Applegreen", "brand_wikidata": "Q7178908"},
        "BP": {"brand": "BP", "brand_wikidata": "Q152057"},
        "Coop": None,
        "ESSO": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "Essar": {"brand": "Essar", "brand_wikidata": "Q5399372"},
        "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
        "JET": {"brand": "JET", "brand_wikidata": "Q568940"},
        "JET ": {"brand": "JET", "brand_wikidata": "Q568940"},
        "Jet": {"brand": "JET", "brand_wikidata": "Q568940"},
        "Morrisons": {"brand": "Morrisons", "brand_wikidata": "Q922344"},
        "Murco": {"brand": "Murco", "brand_wikidata": "Q16998281"},
        "SHELL": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "Sainsbury's": {"brand": "Sainsbury's", "brand_wikidata": "Q152096"},
        "Shell": {"brand": "Shell", "brand_wikidata": "Q110716465"},
        "TESCO": {"brand": "Tesco", "brand_wikidata": "Q487494"},
        "TEXACO": {"brand": "Texaco", "brand_wikidata": "Q775060"},
        "Texaco": {"brand": "Texaco", "brand_wikidata": "Q775060"},
    }

    fuel_map = {
        "B7": "diesel",
        "E10": "e10",
        "E5": "e5",
        # "SDV": "ethanol", # TODO: ?
    }

    def parse(self, response, **kwargs):
        for url in response.xpath("//table/tbody/tr/td[2]/text()").getall():
            yield Request(url, self.parse_locations)

    def parse_locations(self, response, **kwargs):
        for location in response.json()["stations"]:
            item = Feature()
            item["ref"] = location["site_id"]
            item["addr_full"] = location["address"]
            item["postcode"] = location.get("postcode")
            item["lat"] = location["location"]["latitude"]
            item["lon"] = location["location"]["longitude"]

            if brand := self.brand_map.get(location["brand"]):
                item.update(brand)
            else:
                self.crawler.stats.inc_value("atp/gov_cma_fuel_gb/upmapped_brand/{}".format(location["brand"]))

            for fuel, price in location["prices"].items():
                if not price:
                    continue

                if price < 10:
                    # BP, sgnretail, Tesco!
                    price *= 100

                tag = self.fuel_map.get(fuel, fuel)
                item["extras"]["charge:{}".format(tag)] = "{} GBP/1 litre".format(round(price / 100, 2))
                apply_yes_no("fuel:{}".format(tag), item, True)

            apply_category(Categories.FUEL_STATION, item)

            yield item
