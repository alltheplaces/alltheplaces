from locations.spiders.standard_bank_za import StandardBankZASpider

MW_REGIONS = ["Central", "Northern", "Southern"]


class StandardBankMWSpider(StandardBankZASpider):
    name = "standard_bank_mw"
    item_attributes = {"brand": "Standard Bank", "brand_wikidata": "Q1576610"}
    allowed_domains = ["digitalbanking.standardbank.co.za"]
    start_urls = [
        f"https://digitalbanking.standardbank.co.za:8083/sbg-mobile/rest/Communications/geolocator/search?searchTerm={region}&language=en&country=Malawi"
        for region in MW_REGIONS
    ]
