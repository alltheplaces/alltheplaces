import enum
from locations.items import GeojsonPointItem, source_data


class Brand(enum.Enum):
    """
    A wikidata Q-code helps us disambiguate "things". It helps matching with other such disambiguated data sets.
    This enumeration helps us reference "things" in code without typing in numbers which is brittle. The enumeration
    has both name and code point entries which allows it to be checked programmatically against data sets such as
    wikidata itself and also the "name suggestion index".
    """

    CLAIRES = 'Claire\'s', 'Q2974996'
    GAME = 'GAME', 'Q5519813',
    GREGGS = 'Greggs', 'Q3403981',
    LONDIS = 'Londis', 'Q21008564',
    PANDORA = 'Pandora', 'Q2241604',
    PREMIER_STORES = 'Premier', 'Q7240340',
    SPORTS_DIRECT = 'Sports Direct', 'Q7579661'

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: str, brand_wikidata: str):
        self._brand_wikidata_ = brand_wikidata

    def __str__(self):
        return self.value

    def name(self):
        return self._value_

    def brand_wikidata(self):
        return self._brand_wikidata_

    def item(self, response_or_url=None):
        """
        Create a boiler plate POI item based on the brand. A HTTP response structure or URL
        for the POI may optionally be provided in which case extra fields can be filled out
        as a convenience for Spider writers.
        """
        item = GeojsonPointItem()
        item['brand'] = self.value
        item['brand_wikidata'] = self.brand_wikidata()
        if not response_or_url:
            return item
        if isinstance(response_or_url, str):
            url = response_or_url
        else:
            source_data(item, response_or_url)
            url = response_or_url.url

        item['website'] = url
        # Use the individual POI URL as the ref, can always be re-worked in the spider if not appropriate
        item['ref'] = url
        return item
