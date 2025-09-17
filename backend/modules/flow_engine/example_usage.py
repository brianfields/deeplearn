"""
Example usage of the flow_engine module.

This demonstrates how to create flows and steps using the consistent execute() interface.
"""

import asyncio
import traceback
from typing import Any

from pydantic import BaseModel, Field

from .public import BaseFlow, ImageStep, StructuredStep, UnstructuredStep


# Example Steps
class ExtractContentStep(UnstructuredStep):
    """Extract key content from an article."""

    step_name = "extract_content"
    prompt_file = "extract_content.md"

    class Inputs(BaseModel):
        article_text: str = Field(..., description="The article text to extract from")
        max_length: int = Field(default=500, description="Maximum extraction length")


class SummarizeStep(StructuredStep):
    """Create a structured summary of content."""

    step_name = "summarize_content"
    prompt_file = "summarize.md"

    class Inputs(BaseModel):
        content: str = Field(..., description="Content to summarize")
        style: str = Field(default="professional", description="Writing style")

    class Outputs(BaseModel):
        title: str = Field(..., description="Generated title")
        summary: str = Field(..., description="Main summary")
        key_points: list[str] = Field(..., description="Key points extracted")


class CreateThumbnailStep(ImageStep):
    """Generate a thumbnail image."""

    step_name = "create_thumbnail"

    class Inputs(BaseModel):
        prompt: str = Field(..., description="Image generation prompt")
        size: str = Field(default="1024x1024", description="Image size")
        quality: str = Field(default="standard", description="Image quality")


# Example Flow
class ArticleProcessingFlow(BaseFlow):
    """Complete article processing workflow."""

    flow_name = "article_processing"

    class Inputs(BaseModel):
        article_text: str = Field(..., description="The article to process")
        output_style: str = Field(default="professional", description="Output style")
        create_image: bool = Field(default=True, description="Whether to create thumbnail")

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute the complete article processing workflow."""

        # Step 1: Extract key content
        extract_result = await ExtractContentStep().execute({"article_text": inputs["article_text"], "max_length": 400})

        # Step 2: Create structured summary
        summary_result = await SummarizeStep().execute({"content": extract_result.output_content, "style": inputs["output_style"]})

        result = {
            "extracted_content": extract_result.output_content,
            "summary": summary_result.output_content.model_dump(),
            "metadata": {
                "total_tokens": extract_result.metadata["tokens_used"] + summary_result.metadata["tokens_used"],
                "total_cost": extract_result.metadata["cost_estimate"] + summary_result.metadata["cost_estimate"],
                "execution_time_ms": extract_result.metadata["execution_time_ms"] + summary_result.metadata["execution_time_ms"],
            },
        }

        # Step 3: Optionally create thumbnail
        if inputs["create_image"]:
            thumbnail_result = await CreateThumbnailStep().execute({"prompt": f"Thumbnail image for article: {summary_result.output_content.title}", "size": "1024x1024", "quality": "standard"})

            result["thumbnail"] = thumbnail_result.output_content
            result["metadata"]["total_cost"] += thumbnail_result.metadata["cost_estimate"]

        return result


# Example of composable flows
class MasterContentFlow(BaseFlow):
    """Master flow that orchestrates multiple sub-flows."""

    flow_name = "master_content_creation"

    class Inputs(BaseModel):
        articles: list[str] = Field(..., description="List of articles to process")
        batch_style: str = Field(default="professional", description="Style for all articles")

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Process multiple articles using the article processing flow."""

        processed_articles = []
        total_cost = 0.0
        total_tokens = 0

        # Process each article using the sub-flow
        for i, article_text in enumerate(inputs["articles"]):
            article_result = await ArticleProcessingFlow().execute({"article_text": article_text, "output_style": inputs["batch_style"], "create_image": True})

            processed_articles.append({"article_index": i, "summary": article_result["summary"], "thumbnail": article_result.get("thumbnail"), "extracted_content": article_result["extracted_content"]})

            # Aggregate metrics
            total_cost += article_result["metadata"]["total_cost"]
            total_tokens += article_result["metadata"]["total_tokens"]

        return {
            "processed_articles": processed_articles,
            "batch_metadata": {"total_articles": len(inputs["articles"]), "total_cost": total_cost, "total_tokens": total_tokens, "average_cost_per_article": total_cost / len(inputs["articles"]) if inputs["articles"] else 0},
        }


# Usage examples
async def example_single_step() -> None:
    """Example of using a single step."""

    # Execute a single step
    result = await ExtractContentStep().execute({"article_text": "This is a sample article about AI and machine learning...", "max_length": 200})

    print(f"Extracted content: {result.output_content}")
    print(f"Tokens used: {result.metadata['tokens_used']}")
    print(f"Cost: ${result.metadata['cost_estimate']:.4f}")


async def example_single_flow() -> None:
    """Example of using a single flow."""

    # Execute a complete flow
    result = await ArticleProcessingFlow().execute({"article_text": "This is a comprehensive article about the future of artificial intelligence...", "output_style": "academic", "create_image": True})

    print(f"Title: {result['summary']['title']}")
    print(f"Summary: {result['summary']['summary']}")
    print(f"Key points: {result['summary']['key_points']}")
    print(f"Total cost: ${result['metadata']['total_cost']:.4f}")

    if "thumbnail" in result:
        print(f"Thumbnail URL: {result['thumbnail']['image_url']}")


async def example_batch_processing() -> None:
    """Example of batch processing multiple articles."""

    articles = ["Article 1: Introduction to Machine Learning...", "Article 2: Deep Learning Fundamentals...", "Article 3: Natural Language Processing Applications..."]

    # Process multiple articles
    result = await MasterContentFlow().execute({"articles": articles, "batch_style": "technical"})

    print(f"Processed {result['batch_metadata']['total_articles']} articles")
    print(f"Total cost: ${result['batch_metadata']['total_cost']:.4f}")
    print(f"Average cost per article: ${result['batch_metadata']['average_cost_per_article']:.4f}")

    for article in result["processed_articles"]:
        print(f"Article {article['article_index']}: {article['summary']['title']}")


# Main execution
async def main() -> None:
    """Run all examples."""
    print("🚀 Flow Engine Examples")
    print("=" * 50)

    try:
        print("\n1. Single Step Example:")
        await example_single_step()

        print("\n2. Single Flow Example:")
        await example_single_flow()

        print("\n3. Batch Processing Example:")
        await example_batch_processing()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
