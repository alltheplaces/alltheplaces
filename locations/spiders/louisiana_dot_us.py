from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class LouisianaDotUSSpider(NevadaDotUSSpider):
    name = "louisiana_dot_us"
    item_attributes = {"operator": "Louisiana DOT", "operator_wikidata": "Q2400783"}
    start_urls = ["https://511la.org/map/mapIcons/Cameras"]
