from locations.storefinders.yext import YextSpider


class IbisNLSpider(YextSpider):
    name = "ibis_nl"
    item_attributes = {"brand": "Ibis", "brand_wikidata": "Q920166"}
    api_key = "f60a800cdb7af0904b988d834ffeb221"
    wanted_types = ["hotel"]
    search_filter = {"name": {"$contains": "Ibis"}, "countryCode": "NL"}
