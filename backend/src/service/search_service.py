from typing import Dict, Any, Optional
from elasticsearch import AsyncElasticsearch
from ..utils.logs.error_handling import CustomLogger, AppException
from fastapi import status

class SearchService:
    def __init__(self, client: AsyncElasticsearch, logger: CustomLogger):
        self.client = client
        self.logger = logger

    def build_fuzzy_query(self, search_term: str, fuzziness: str, operator: str) -> Dict[str, Any]:
        return {
            "query": {
                "nested": {
                    "path": "pages",
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "pages.content": {
                                            "query": search_term,
                                            "fuzziness": fuzziness,
                                            "operator": operator.upper(),
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    "inner_hits": {
                        "highlight": {
                            "fields": {
                                "pages.content": {
                                    "number_of_fragments": 3,
                                    "fragment_size": 150,
                                    "pre_tags": ["<mark>"],
                                    "post_tags": ["</mark>"]
                                }
                            }
                        }
                    }
                }
            },
            "_source": ["filename", "relative_path", "total_pages", "metadata", "pages"],
            "size": 10
        }

    def build_exact_query(self, search_term: str) -> Dict[str, Any]:
        return {
            "query": {
                "nested": {
                    "path": "pages",
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "match_phrase": {
                                        "pages.content": search_term
                                    }
                                }
                            ]
                        }
                    },
                    "inner_hits": {
                        "highlight": {
                            "fields": {
                                "pages.content": {
                                    "number_of_fragments": 3,
                                    "fragment_size": 150
                                }
                            }
                        }
                    }
                }
            },
            "_source": ["filename", "relative_path", "total_pages", "metadata", "pages"],
            "size": 10
        }

    def build_match_all_query(self) -> Dict[str, Any]:
        return {
            "query": {"match_all": {}},
            "_source": ["filename", "relative_path", "total_pages", "metadata"]
        }

    async def execute_search(self, index_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self.client.search(index=index_name, body=query)
        except Exception as e:
            self.logger.error("Error ejecutando búsqueda en Elasticsearch", error=e)
            raise AppException(
                message="Error al realizar la búsqueda",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                extra={"elasticsearch_error": str(e)}
            )

    def process_search_results(self, response: Dict[str, Any], search_term: Optional[str] = None) -> Dict[str, Any]:
        formatted_results = {
            "total_hits": response["hits"]["total"]["value"],
            "results": []
        }

        for hit in response["hits"]["hits"]:
            try:
                doc_result = self._process_document(hit, search_term)
                formatted_results["results"].append(doc_result)
                
            except KeyError as ke:
                self.logger.warning(
                    "Error procesando documento",
                    {"document_id": hit.get("_id"), "missing_field": str(ke)}
                )
                continue

        return formatted_results

    def _process_document(self, hit: Dict[str, Any], search_term: Optional[str]) -> Dict[str, Any]:
        doc_result = {
            "filename": hit["_source"]["filename"],
            "relative_path": hit["_source"]["relative_path"],
            "total_pages": hit["_source"]["total_pages"],
            "metadata": hit["_source"]["metadata"],
            "matching_pages": [],
            "score": hit.get("_score")
        }

        if search_term and "inner_hits" in hit:
            doc_result["matching_pages"] = self._process_matching_pages(hit["inner_hits"]["pages"]["hits"]["hits"])

        return doc_result

    def _process_matching_pages(self, inner_hits: list) -> list:
        matching_pages = []
        for inner_hit in inner_hits:
            page_content = inner_hit["_source"]
            highlights = inner_hit.get("highlight", {}).get("pages.content", [])
            
            matching_pages.append({
                "page_number": page_content["number"],
                "content": page_content["content"],
                "highlights": highlights,
                "score": inner_hit.get("_score")
            })
        return matching_pages