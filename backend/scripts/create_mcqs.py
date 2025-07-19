#!/usr/bin/env python3
"""
Command Line Script for MCQ Creation

This script creates MCQs from unstructured material using the two-pass approach:
1. Extract refined material from source text
2. Create individual MCQs for each topic/learning objective
3. Evaluate each MCQ for quality

Example Usage:
    # Create MCQs about PyTorch tensor usage (reference material included)
    python scripts/create_mcqs.py --topic "PyTorch Tensor Usage" --file scripts/examples/pytorch_tensor_material.txt --output scripts/examples/pytorch_mcqs.json --domain "Machine Learning" --level intermediate --verbose

    # Basic usage
    python scripts/create_mcqs.py --topic "Your Topic" --file your_material.txt

    # With all options
    python scripts/create_mcqs.py --topic "Advanced Python" --file python_material.txt --output results.json --domain "Programming" --level advanced --verbose

Arguments:
    --topic: Topic title for the MCQs (required)
    --file: Path to text file containing source material (required)
    --output: Output JSON file path (default: mcqs_output.json)
    --domain: Subject domain (optional)
    --level: Target user level (beginner/intermediate/advanced, default: intermediate)
    --model: LLM model to use (default: gpt-4)
    --verbose: Show detailed progress and results
"""

import argparse
import json
import sys
import asyncio
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.modules.lesson_planning.bite_sized_topics.mcq_service import MCQService


async def main():
    parser = argparse.ArgumentParser(description='Create MCQs from unstructured material')
    parser.add_argument('--topic', required=True, help='Topic title for the MCQs')
    parser.add_argument('--file', required=True, help='Path to text file containing source material')
    parser.add_argument('--output', help='Output JSON file path (default: mcqs_output.json)')
    parser.add_argument('--domain', default='', help='Subject domain (optional)')
    parser.add_argument('--level', default='intermediate',
                       choices=['beginner', 'intermediate', 'advanced'],
                       help='Target user level')
    parser.add_argument('--model', default='gpt-4o', help='LLM model to use')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Validate input file
    input_file = Path(args.file)
    if not input_file.exists():
        print(f"Error: Input file '{args.file}' not found")
        sys.exit(1)

    # Set output file
    output_file = Path(args.output) if args.output else Path('mcqs_output.json')

    # Read source material
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source_material = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    if not source_material.strip():
        print("Error: Input file is empty")
        sys.exit(1)

    # Initialize services
    from src.core.llm_client import create_llm_client
    import os

    # Get API key from environment variable
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("Using dummy key for testing purposes.")
        api_key = "dummy_key"

    llm_client = create_llm_client(
        api_key=api_key,
        model=args.model
    )
    mcq_service = MCQService(llm_client)
    context = PromptContext(
        user_level=args.level,
        time_constraint=30  # 30 minutes for MCQ creation
    )

    print(f"Creating MCQs for topic: {args.topic}")
    print(f"Source material length: {len(source_material)} characters")
    print(f"Target level: {args.level}")
    if args.domain:
        print(f"Domain: {args.domain}")
    print()

    try:
        print("🔍 Starting two-pass MCQ creation...")
        print("📝 Pass 1: Extracting refined material from source text...")

        # Create MCQs using two-pass approach
        refined_material, mcqs_with_evaluations = await mcq_service.create_mcqs_from_text(
            source_material=source_material,
            topic_title=args.topic,
            domain=args.domain,
            user_level=args.level,
            context=context
        )

        print(f"✅ Pass 1 completed: Found {len(refined_material.get('topics', []))} topics")
        print(f"🧪 Pass 2: Created {len(mcqs_with_evaluations)} MCQs")
        print("📊 Pass 3: Quality evaluation completed")

        # Prepare output
        output_data = {
            'topic': args.topic,
            'domain': args.domain,
            'user_level': args.level,
            'source_material_length': len(source_material),
            'refined_material': refined_material,
            'mcqs': mcqs_with_evaluations,
            'summary': {
                'total_topics': len(refined_material.get('topics', [])),
                'total_mcqs': len(mcqs_with_evaluations),
                'topics_covered': [topic.get('topic', '') for topic in refined_material.get('topics', [])]
            }
        }

        # Save output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Print summary
        print(f"\n🎉 Success! Created {len(mcqs_with_evaluations)} MCQs")
        print(f"📚 Refined material extracted for {len(refined_material.get('topics', []))} topics")
        print(f"💾 Results saved to: {output_file}")

        if args.verbose:
            print("\n📋 Topics covered:")
            for topic in refined_material.get('topics', []):
                topic_name = topic.get('topic', '')
                objectives_count = len(topic.get('learning_objectives', []))
                print(f"  - {topic_name} ({objectives_count} learning objectives)")

            print("\n🎯 MCQ Quality Summary:")
            for i, mcq_data in enumerate(mcqs_with_evaluations, 1):
                evaluation = mcq_data['evaluation']
                overall_quality = evaluation.get('overall', 'No evaluation available')
                print(f"  MCQ {i}: {overall_quality[:80]}{'...' if len(overall_quality) > 80 else ''}")

            print(f"\n📊 Summary Statistics:")
            print(f"  - Total characters processed: {len(source_material):,}")
            print(f"  - Topics identified: {len(refined_material.get('topics', []))}")
            print(f"  - MCQs created: {len(mcqs_with_evaluations)}")
            print(f"  - Target level: {args.level}")
            print(f"  - Domain: {args.domain or 'General'}")

        print(f"\n🔍 To view detailed results, check: {output_file}")

    except Exception as e:
        print(f"Error creating MCQs: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())