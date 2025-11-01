"""Scheduler and action orchestrator with jitter and safe execution."""

from __future__ import annotations

import random
import time
from datetime import datetime
from typing import Any, Optional

import yaml

from budget import BudgetManager
from storage import Storage
from x_client import XClient


class Scheduler:
    """Schedule and execute agent actions."""

    def __init__(
        self,
        client: XClient,
        storage: Storage,
        budget: BudgetManager,
        config: dict[str, Any],
    ):
        self.client = client
        self.storage = storage
        self.budget = budget
        self.config = config

    @classmethod
    def from_config(
        cls,
        config_path: str,
        client: XClient,
        storage: Storage,
        budget: BudgetManager,
    ) -> Scheduler:
        """Load scheduler from YAML config."""
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return cls(client, storage, budget, config)

    def run_post_actions(self) -> None:
        """Execute posting actions."""
        post_config = self.config.get("actions", {}).get("post", {})
        
        if not post_config.get("enabled", False):
            print("Posting actions disabled in config")
            return

        max_posts = post_config.get("max_per_run", 1)
        topics = post_config.get("topics", [])
        
        if not topics:
            print("No topics configured for posting")
            return

        print(f"\n=== Running Post Actions (max: {max_posts}) ===")
        
        for i in range(max_posts):
            # Random topic
            topic = random.choice(topics)
            
            # Generate post text (placeholder - extend with LLM/templates)
            text = self._generate_post_text(topic)
            
            # Check for duplicates
            if self.storage.is_text_duplicate(text):
                print(f"⚠️  Skipping duplicate text")
                continue
            
            try:
                # Create post
                result = self.client.create_post(text)
                post_id = result.get("data", {}).get("id", "unknown")
                
                print(f"✓ Posted: {text[:50]}... (ID: {post_id})")
                
                # Log action
                self.storage.log_action(
                    kind="create_post",
                    post_id=post_id,
                    text=text,
                    topic=topic,
                    status="success",
                )
                
                # Store hash
                self.storage.store_text_hash(text)
                
                # Add jitter between posts
                if i < max_posts - 1:
                    self.client.rate_limiter.add_jitter(8000, 20000)
                
            except Exception as e:
                print(f"❌ Post failed: {e}")
                self.storage.log_action(
                    kind="create_post",
                    text=text,
                    topic=topic,
                    status=f"failed: {e}",
                )

    def run_interact_actions(self) -> None:
        """Execute interaction actions (search, reply, like, follow)."""
        interact_config = self.config.get("actions", {}).get("interact", {})
        
        if not interact_config.get("enabled", False):
            print("Interaction actions disabled in config")
            return

        queries = interact_config.get("queries", [])
        max_results_per_query = interact_config.get("max_results_per_query", 5)
        
        if not queries:
            print("No queries configured for interaction")
            return

        print(f"\n=== Running Interact Actions ===")
        
        # Get authenticated user ID
        if not self.client.me_id:
            me_info = self.client.get_me()
            self.client.me_id = me_info.get("data", {}).get("id")
        
        for query_config in queries:
            query = query_config.get("query", "")
            actions = query_config.get("actions", [])
            
            if not query:
                continue
            
            print(f"\nSearching: {query}")
            
            try:
                # Search recent posts
                results = self.client.search_recent(query, max_results=max_results_per_query)
                posts = results.get("data", [])
                
                print(f"Found {len(posts)} posts")
                
                # Process each post
                for post in posts:
                    post_id = post["id"]
                    author_id = post.get("author_id")
                    text = post.get("text", "")
                    
                    print(f"  Post {post_id}: {text[:60]}...")
                    
                    # Execute configured actions
                    for action in actions:
                        try:
                            if action == "like":
                                self.client.like_post(self.client.me_id, post_id)
                                print(f"    ✓ Liked")
                                self.storage.log_action(kind="like", post_id=post_id, ref_id=author_id)
                            
                            elif action == "reply":
                                reply_text = self._generate_reply_text(text, query)
                                if not self.storage.is_text_duplicate(reply_text):
                                    self.client.create_post(reply_text, reply_to=post_id)
                                    print(f"    ✓ Replied")
                                    self.storage.log_action(kind="reply", post_id=post_id, text=reply_text)
                                    self.storage.store_text_hash(reply_text)
                            
                            elif action == "repost" and author_id:
                                self.client.repost(self.client.me_id, post_id)
                                print(f"    ✓ Reposted")
                                self.storage.log_action(kind="repost", post_id=post_id, ref_id=author_id)
                            
                            elif action == "follow" and author_id:
                                self.client.follow_user(self.client.me_id, author_id)
                                print(f"    ✓ Followed @{author_id}")
                                self.storage.log_action(kind="follow", ref_id=author_id)
                            
                            # Jitter between actions
                            self.client.rate_limiter.add_jitter(2000, 5000)
                            
                        except Exception as e:
                            print(f"    ❌ {action} failed: {e}")
                            self.storage.log_action(kind=action, post_id=post_id, status=f"failed: {e}")
                    
                    # Longer jitter between posts
                    self.client.rate_limiter.add_jitter(8000, 20000)
                
            except Exception as e:
                print(f"❌ Search failed: {e}")

    def settle_metrics(self) -> None:
        """Fetch and store metrics for recent posts."""
        print("\n=== Settling Metrics ===")
        
        # Get recent create_post actions
        actions = self.storage.get_recent_actions(kind="create_post", limit=50)
        
        for action in actions:
            post_id = action.get("post_id")
            if not post_id or post_id == "unknown":
                continue
            
            try:
                # Fetch tweet with metrics
                result = self.client.get_tweet(post_id, tweet_fields=["public_metrics"])
                metrics = result.get("data", {}).get("public_metrics", {})
                
                # Store metrics
                self.storage.update_metrics(
                    post_id=post_id,
                    like_count=metrics.get("like_count", 0),
                    reply_count=metrics.get("reply_count", 0),
                    retweet_count=metrics.get("retweet_count", 0),
                    quote_count=metrics.get("quote_count", 0),
                    impression_count=metrics.get("impression_count", 0),
                )
                
                print(f"✓ Settled metrics for {post_id}: {metrics}")
                
                # Jitter
                self.client.rate_limiter.add_jitter(1000, 3000)
                
            except Exception as e:
                print(f"❌ Failed to settle {post_id}: {e}")

    def _generate_post_text(self, topic: str) -> str:
        """Generate post text for a topic (placeholder).
        
        In production, integrate with LLM or template system.
        """
        templates = [
            f"Exploring {topic} today. Fascinating insights! #tech",
            f"Just learned something new about {topic}. Game changer! 🚀",
            f"Thoughts on {topic}? Would love to hear your perspective.",
        ]
        return random.choice(templates)

    def _generate_reply_text(self, original_text: str, context: str) -> str:
        """Generate reply text (placeholder).
        
        In production, use LLM for context-aware replies.
        """
        templates = [
            "Interesting perspective! Thanks for sharing.",
            "Great point! I've been thinking about this too.",
            "This is valuable. Appreciate the insights! 💡",
        ]
        return random.choice(templates)
