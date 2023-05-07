from locations.spiders.calvin_klein import CalvinKleinSpider
from locations.storefinders.where2getit import Where2GetItSpider


class CalvinKleinCAUSSpider(Where2GetItSpider):
    name = "calvin_klein_ca_us"
    item_attributes = CalvinKleinSpider.item_attributes
    api_brand_name = "calvinklein"
    api_key = "F5C66E24-E944-11EA-A1DF-53CCF48ECC77"
    api_filter = {"or": {"icon": {"like": ""}}}
