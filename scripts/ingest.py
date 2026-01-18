#!/usr/bin/env python3
"""CLI script for ingesting documents into the knowledge base."""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.pipeline import get_pipeline
from app.core.vectorstore import get_collection_stats


def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents into the Cultural AI knowledge base"
    )
    
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        help="Path to file or directory to ingest"
    )
    
    parser.add_argument(
        "--url",
        "-u",
        type=str,
        help="URL to ingest"
    )
    
    parser.add_argument(
        "--category",
        "-c",
        type=str,
        default="general",
        help="Category tag for the documents (default: general)"
    )
    
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        default=True,
        help="Recursively search directories (default: True)"
    )
    
    parser.add_argument(
        "--stats",
        "-s",
        action="store_true",
        help="Show knowledge base statistics"
    )
    
    args = parser.parse_args()
    
    # Show stats if requested
    if args.stats:
        stats = get_collection_stats()
        print(f"\n[STATS] Knowledge Base Statistics:")
        print(f"   Collection: {stats['name']}")
        print(f"   Documents: {stats['count']}")
        return
    
    # Need either path or URL
    if not args.path and not args.url:
        parser.print_help()
        print("\n[WARN] Please provide either --path or --url")
        return
    
    pipeline = get_pipeline(verbose=True)
    
    # Ingest URL
    if args.url:
        print(f"\n[URL] Ingesting URL: {args.url}")
        chunks = pipeline.ingest_url(args.url, category=args.category)
        print(f"\n[DONE] Ingested {chunks} chunks from URL")
    
    # Ingest path (file or directory)
    if args.path:
        path = os.path.abspath(args.path)
        
        if not os.path.exists(path):
            print(f"[ERROR] Path not found: {path}")
            return
        
        if os.path.isfile(path):
            print(f"\n[FILE] Ingesting file: {path}")
            chunks = pipeline.ingest_file(path, category=args.category)
            print(f"\n[DONE] Ingested {chunks} chunks from file")
        else:
            print(f"\n[DIR] Ingesting directory: {path}")
            chunks = pipeline.ingest_directory(
                path,
                category=args.category,
                recursive=args.recursive
            )
            print(f"\n[DONE] Ingested {chunks} chunks from directory")
    
    # Show final stats
    stats = get_collection_stats()
    print(f"\n[STATS] Total documents in knowledge base: {stats['count']}")


if __name__ == "__main__":
    main()
