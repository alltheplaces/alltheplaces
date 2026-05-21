from locations.storefinders.yext_answers import YextAnswersSpider


class AveraUSSpider(YextAnswersSpider):
    name = "avera_us"
    item_attributes = {"operator": "Avera Health", "operator_wikidata": "Q4828238"}
    experience_key = "locator"
    api_key = "413a34db5016c35c9f4a790833a03dd3"
