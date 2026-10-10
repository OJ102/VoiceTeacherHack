import os
from tavily import TavilyClient


class TavilySearch:
    def __init__(self):
        self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    def search_for_teaching(self, topic: str) -> dict:
        """Search Tavily for facts to ground teaching response."""
        try:
            query = f"Python {topic} basics explanation with examples"
            results = self.client.search(
                query=query,
                max_results=3,
                include_answer=True,
            )
            return {
                "success": True,
                "query": query,
                "results": results.get("results", []),
                "answer": results.get("answer", ""),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "answer": "",
            }

    def format_facts_for_prompt(self, search_results: dict) -> str:
        """Format search results into a concise fact block for LLM prompt."""
        if not search_results["success"] or not search_results["results"]:
            return "No web sources found."

        facts = []
        for result in search_results["results"][:2]:  # Top 2 results
            facts.append(f"- {result.get('title', 'Source')}: {result.get('content', '')[:150]}...")

        return "\n".join(facts) if facts else "No relevant facts found."
