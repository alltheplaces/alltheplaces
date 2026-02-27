from locations.spiders.calvin_klein import CalvinKleinSpider
from locations.storefinders.yext_answers import YextAnswersSpider


class CalvinKleinUSSpider(YextAnswersSpider):
    name = "calvin_klein_us"
    item_attributes = CalvinKleinSpider.item_attributes
    api_key = "e922a5467c105dbc672e892b1c6a6564"
    experience_key = "calvin-klein-locator-usa"
    feature_type = "usa-locations"
    locale = "en-US"
