from locations.spiders.standard_bank_za import StandardBankZASpider

ZW_PROVINCES = [
    "Bulawayo",
    "Harare",
    "Manicaland",
    "Mashonaland Central",
    "Mashonaland East",
    "Mashonaland West",
    "Masvingo",
    "Matabeleland North",
    "Matabeleland South",
    "Midlands",
]


class StandardBankZWSpider(StandardBankZASpider):
    name = "standard_bank_zw"
    item_attributes = {"brand": "Standard Bank", "brand_wikidata": "Q1576610"}
    allowed_domains = ["digitalbanking.standardbank.co.za"]
    start_urls = [
        f"https://digitalbanking.standardbank.co.za:8083/sbg-mobile/rest/Communications/geolocator/search?searchTerm={province}&language=en&country=Zimbabwe"
        for province in ZW_PROVINCES
    ]
