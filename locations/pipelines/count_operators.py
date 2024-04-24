class CountOperatorsPipeline:
    def process_item(self, item, spider):
        if operator := item.get("operator"):
            spider.crawler.stats.inc_value(f"atp/operator/{operator}")
        if wikidata := item.get("operator_wikidata"):
            spider.crawler.stats.inc_value(f"atp/operator_wikidata/{wikidata}")
        return item
