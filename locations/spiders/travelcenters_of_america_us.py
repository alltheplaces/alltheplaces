import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class TravelcentersOfAmericaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "travelcenters_of_america_us"
    allowed_domains = ["www.ta-petro.com"]
    sitemap_urls = ["https://www.ta-petro.com/sitemap-xml/"]
    sitemap_rules = [(r"\/location\/\w{2}\/[\w\-]+\/$", "parse_sd")]
    brands = {
        "/petro-": {"brand": "Petro", "brand_wikidata": "Q64051305"},
        "/ta-express-": {"brand": "TA Express", "brand_wikidata": "Q7835892"},
        "/ta-": {"brand": "TA", "brand_wikidata": "Q7835892"},
    }

    def post_process_item(self, item, response, ld_data):
        for brand_key, brand_attributes in self.brands.items():
            if brand_key in response.url:
                item.update(brand_attributes)
                break
        if m := re.search(r"#(\d{4})$", item["name"]):
            item["ref"] = m.group(1)
        item.pop("facebook", None)
        item.pop("twitter", None)
        fuel_types = []
        if (
            ld_data.get("hasOfferCatalog")
            and ld_data["hasOfferCatalog"].get("name") == "Fuel"
            and ld_data["hasOfferCatalog"].get("itemListElement")
        ):
            for fuel_type in ld_data["hasOfferCatalog"]["itemListElement"]:
                fuel_types.append(fuel_type["name"])
        apply_category(Categories.FUEL_STATION, item)
        apply_yes_no(Fuel.OCTANE_87, item, "Unleaded" in fuel_types, False)
        apply_yes_no(Fuel.OCTANE_89, item, "Unleaded Plus" in fuel_types, False)
        apply_yes_no(Fuel.OCTANE_93, item, "Unleaded Premium" in fuel_types, False)
        apply_yes_no(
            Fuel.BIODIESEL,
            item,
            "BIO DIESEL 2% ULS" in fuel_types
            or "BIO DIESEL 5% ULS" in fuel_types
            or "BIO DIESEL 10% ULS" in fuel_types
            or "BIO DIESEL 11% ULS" in fuel_types
            or "BIO DIESEL 20% ULS" in fuel_types
            or "TEX LED ULSD #2 - 20% BIO" in fuel_types
            or "20%BIO DSL - CA CARB ULSD#2" in fuel_types,
            False,
        )
        apply_yes_no(
            Fuel.DIESEL,
            item,
            "Auto Diesel" in fuel_types
            or "Diesel" in fuel_types
            or "Diesel 1" in fuel_types
            or "Diesel 1 Reefer" in fuel_types
            or "Reefer" in fuel_types
            or "Offroad Diesel" in fuel_types
            or "TEX LED ULSD #2" in fuel_types,
            False,
        )
        apply_yes_no(
            Fuel.COLD_WEATHER_DIESEL,
            item,
            "DIESEL #2 SELF ULS" in fuel_types
            or "TEX LED ULSD #2 - 20% BIO" in fuel_types
            or "20%BIO DSL - CA CARB ULSD#2" in fuel_types,
            False,
        )
        apply_yes_no(Fuel.ADBLUE, item, "DEF" in fuel_types, False)
        apply_yes_no(
            Fuel.LNG,
            item,
            "SHELL LNG 3" in fuel_types
            or "Shell LNG 3" in fuel_types
            or "SHELL LNG 7" in fuel_types
            or "Shell LNG 7" in fuel_types,
            False,
        )
        yield item
