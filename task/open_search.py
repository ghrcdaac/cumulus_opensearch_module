from dataclasses import dataclass
import requests
import os

from task.logger import ops_logger

logger = ops_logger

@dataclass
class CumulusOpenSearch:
    """
    Class to interact with Cumulus OpenSearch
    """
    opensearch_index: str = os.getenv("OPENSEARCH_INDEX")
    opensearch_base_url: str = os.getenv("OPENSEARCH_BASE_URL")

    def __init__(self, record_type='granule'):
        self.opensearch_base_url = self.opensearch_base_url.rstrip('/')
        self.opensearch_url = f"{self.opensearch_base_url}/{self.opensearch_index}/{record_type}/_search"

    @staticmethod
    def generate_match_pharse_query(**kwargs):
        """
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        match_query: list = []
        for key, value in kwargs.items():
            is_a = "terms" if isinstance(value, list) else "match_phrase"
            match_query.append({is_a: {key: value}})
        query = {
            "query": {
                "bool": {
                    "must": match_query.copy()
                }
            }
        }
        return query

    def query_opensearch(self, size: int = 10000, terminate_after=0, query=None, **kwargs):
        """
        Query OpenSearch with a prebuilt query or pass query terms in kwargs and a match phrase query will be created.

        :param terminate_after: The maximum number of documents OpenSearch should process before terminating the
        request. Default is 0.
        :param query: A pre-constructed OpenSearch query.
        :param size: How many results to include in an OpenSearch response. The default is 10000.
        :return: A python generator that will yield all matching records.
        """
        url = f'{self.opensearch_url}/?scroll=5m&terminate_after={int(terminate_after)}&size={size}'
        logger.info(f'OpenSearch query: {str(query)}')
        logger.info(f'OpenSearch url: {url}')

        results = requests.post(url, json=query)
        if not results.ok:
            print(results.content)
            return

        while True:
            data = results.json()
            scroll_id = data['_scroll_id']
            hits = data['hits']['hits']
            if hits:
                yield hits
                results = self.search_by_scroll(scroll_id)
            else:
                cleaning_up_scroll = self.clear_scroll(scroll_id)
                if not cleaning_up_scroll.ok:
                    print('Error clearing the scroll')
                break
        return

    def search_by_scroll(self, scroll_id: str):
        """
        Search by a scroll id
        :param scroll_id:
        :type scroll_id:
        :return: scroll id
        :rtype:
        """
        url = f"{self.opensearch_base_url}/_search/scroll"
        return requests.post(url, json={"scroll": "10m", "scroll_id": scroll_id})

    def clear_scroll(self, scroll_id: str):
        """
        Delete scroll id
        :param scroll_id:
        :type scroll_id:
        :return:
        :rtype:
        """
        url = f"{self.opensearch_base_url}/_search/scroll"
        response = requests.delete(url, json={"scroll_id": [scroll_id]})
        return response

    @staticmethod
    def generate_inline_script(set_record_kwargs):
        """

        :return:
        :rtype:
        """
        inline_update = ";".join([f"ctx._source.{key}=params.{key}" for key in set_record_kwargs.keys()])
        return {"script": {
            "inline": inline_update,
            "lang": "painless",
            "params": set_record_kwargs
        }}

    def update_opensearch_by_query(self, query_kwargs, set_record_kwargs=None):
        """
        :param query:
        :type query:
        :param set_record:
        :type set_record:
        :return:
        :rtype:
        """
        url = f"{self.opensearch_url}/_update_by_query"
        record_to_post = self.generate_match_pharse_query(**query_kwargs)

        record_to_post.update(self.generate_inline_script(set_record_kwargs))

        response = requests.post(url, json=record_to_post)
        return response

    def delete_opensearch_by_query(self, query=None, **kwargs):
        """
        Delete from opensearch by query
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        url = f"{self.opensearch_url}/_delete_by_query"
        record_to_delete = query if query else self.generate_match_pharse_query(**kwargs)
        response = requests.post(url, json=record_to_delete)
        return response


if __name__ == '__main__':
    pass
