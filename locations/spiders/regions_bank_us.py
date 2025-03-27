import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class RegionsBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "regions_bank_us"
    item_attributes = {
        "brand": "Regions Bank",
        "brand_wikidata": "Q917131",
    }
    sitemap_urls = ["https://www.regions.com/sitemap.xml"]
    sitemap_rules = [
        (r"^https://www.regions.com/locator/[a-z]{2}/[\w-]+/[\w-]+$", "parse"),
    ]
    search_for_facebook = False
    search_for_twitter = False
    search_for_amenity_features = False

    def pre_process_data(self, ld_data):
        if opening_hours_specification := ld_data.get("openingHoursSpecification"):
            if rules := opening_hours_specification.get("dayOfWeek"):
                ld_data["openingHoursSpecification"] = rules

    def post_process_item(self, item, response, ld_data, **kwargs):
        search_results = chompjs.parse_js_object(
            response.xpath("//script[contains(text(), 'window.searchResults')]/text()").get()
        )
        item["lat"] = search_results[0]["lat"]
        item["lon"] = search_results[0]["lng"]

        if ld_data["@type"] == "BankOrCreditUnion":
            apply_category(Categories.BANK, item)
        elif ld_data["@type"] == "AutomatedTeller":
            apply_category(Categories.ATM, item)

        _, _, item["branch"] = item.pop("name").partition(" - ")

        apply_yes_no(
            Extras.ATM, item, any(place["@type"] == "AutomatedTeller" for place in ld_data.get("containsPlace", []))
        )
        apply_yes_no(Extras.DRIVE_THROUGH, item, ld_data.get("hasDriveThroughService") == "True")

        for language in ld_data.get("knowsLanguage", []):
            if lang_name := language.get("alternateName"):
                apply_yes_no(f"language:{lang_name}", item, True)

        yield item
