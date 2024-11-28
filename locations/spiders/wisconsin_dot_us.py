from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class WisconsinDotUSSpider(NevadaDotUSSpider):
    name = "wisconsin_dot_us"
    item_attributes = {"operator": "Wisconsin DOT", "operator_wikidata": "Q8027162"}
    start_urls = ["https://511wi.gov/map/mapIcons/Cameras"]
