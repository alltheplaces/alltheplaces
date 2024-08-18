from locations.storefinders.location_bank import LocationBankSpider
from locations.categories import Categories

class LocationBankCompanySpider(LocationBankSpider):
    name = "location_bank_company"
    client_id = "8dca5bbb-f571-46d5-a65b-cdd5cc6d4953"
    item_attributes = {"brand": "Location Bank", "brand_wikidata": "Q129264350", "extras": Categories.OFFICE_COMPANY.value}