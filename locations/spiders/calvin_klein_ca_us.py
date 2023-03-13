from locations.spiders.calvin_klein import CalvinKleinSpider
from locations.storefinders.where2getit import Where2GetItSpider


class CalvinKleinCAUSSpider(Where2GetItSpider):
    name = "calvin_klein_us"
    item_attributes = CalvinKleinSpider.item_attributes
    w2gi_id = "F5C66E24-E944-11EA-A1DF-53CCF48ECC77"
    w2gi_filter = {"or": {"icon": {"like": ""}}}
    w2gi_query = "CA"
