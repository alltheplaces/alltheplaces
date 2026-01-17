class CountLocatedInPipeline:
    def process_item(self, item, spider):
        if located_in := item.get("located_in"):
            spider.crawler.stats.inc_value(f"atp/located_in/{located_in}")
        if wikidata := item.get("located_in_wikidata"):
            spider.crawler.stats.inc_value(f"atp/located_in_wikidata/{wikidata}")
        return item
