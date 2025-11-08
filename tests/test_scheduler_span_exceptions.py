"""Coverage tests for scheduler.py exception handlers around span.set_attribute."""

from unittest.mock import MagicMock, patch

from scheduler import run_interact_actions, run_post_action, run_scheduler


class TestSchedulerSpanExceptions:
    """Tests to cover exception handlers in scheduler functions."""

    @patch("scheduler.start_span")
    @patch("scheduler.choose_template")
    def test_run_post_action_span_set_attribute_exceptions(self, mock_template, mock_start_span):
        """Test run_post_action handles span.set_attribute exceptions gracefully (covers lines 80-81)."""
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_storage.is_text_duplicate.return_value = False
        mock_template.return_value = "Test post content"

        # Create a span that raises exceptions on set_attribute
        # Use side_effect list: first call succeeds, second fails (triggering except on lines 80-81)
        mock_span = MagicMock()
        mock_span.set_attribute.side_effect = [
            None,  # First call succeeds
            RuntimeError("Span error"),  # Second call fails, caught by except on line 80-81
        ]
        mock_start_span.return_value.__enter__.return_value = mock_span
        mock_start_span.return_value.__exit__.return_value = None

        config = {
            "schedule": {"windows": ["morning"]},
            "topics": ["test"],
            "learning": {"enabled": False},
        }

        # Should complete without raising exception despite span errors (exception caught on lines 80-81)
        run_post_action(mock_client, mock_storage, config, dry_run=True)

        # Verify span.set_attribute was called twice (second one raised exception caught by lines 80-81)
        assert mock_span.set_attribute.call_count == 2  # slot (success), topic (exception caught)

    @patch("scheduler.start_span")
    @patch("scheduler.choose_template")
    def test_run_post_action_duplicate_detection_span_exception(self, mock_template, mock_start_span):
        """Test duplicate detection span.set_attribute exception handling (covers lines 91-92)."""
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_storage.is_text_duplicate.return_value = True  # Trigger duplicate path
        mock_template.return_value = "Duplicate content"

        # Create a span that raises exceptions on set_attribute
        mock_span = MagicMock()
        mock_span.set_attribute.side_effect = RuntimeError("Span attribute error")
        mock_start_span.return_value.__enter__.return_value = mock_span
        mock_start_span.return_value.__exit__.return_value = None

        config = {
            "schedule": {"windows": ["morning"]},
            "topics": ["test"],
            "learning": {"enabled": False},
        }

        # Should return early due to duplicate but handle span exception
        run_post_action(mock_client, mock_storage, config, dry_run=True)

        # Verify the duplicate attribute was attempted to be set
        assert mock_span.set_attribute.call_count > 0

    @patch("scheduler.start_span")
    @patch("scheduler.act_on_search")
    def test_run_interact_actions_query_span_exception(self, mock_act, mock_start_span):
        """Test run_interact_actions handles query span.set_attribute exceptions (covers lines 189-190)."""
        mock_client = MagicMock()
        mock_client.get_me.return_value = {"data": {"id": "123"}}
        mock_storage = MagicMock()
        mock_act.return_value = {"like": 0, "reply": 0, "repost": 0}

        # Outer span works fine
        outer_span = MagicMock()
        # Query span raises exceptions
        query_span = MagicMock()
        query_span.set_attribute.side_effect = RuntimeError("Query span error")

        # Return different spans for different calls
        mock_start_span.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=outer_span), __exit__=MagicMock(return_value=None)),
            MagicMock(__enter__=MagicMock(return_value=query_span), __exit__=MagicMock(return_value=None)),
        ]

        config = {
            "queries": ["test query"],
            "limits": {"like": 1, "reply": 0, "repost": 0},
        }

        # Should complete without raising exception
        run_interact_actions(mock_client, mock_storage, config, dry_run=True)

        # Verify query span attribute was attempted
        assert query_span.set_attribute.called

    @patch("scheduler.start_span")
    @patch("scheduler.run_post_action")
    @patch("scheduler.run_interact_actions")
    def test_run_scheduler_span_exceptions(self, mock_interact, mock_post, mock_start_span):
        """Test run_scheduler handles span.set_attribute exceptions (covers lines 220-221)."""
        mock_client = MagicMock()
        mock_storage = MagicMock()

        # Create a span that raises exceptions on set_attribute
        mock_span = MagicMock()
        mock_span.set_attribute.side_effect = [
            None,  # First call succeeds
            RuntimeError("Span error"),  # Second call fails, caught by except on line 220-221
        ]
        mock_start_span.return_value.__enter__.return_value = mock_span
        mock_start_span.return_value.__exit__.return_value = None

        config = {
            "cadence": {"weekdays": [1, 2, 3, 4, 5]},  # Mon-Fri
        }

        # Mock datetime to be a weekday
        with patch("scheduler.datetime") as mock_dt:
            mock_dt.today.return_value.isoweekday.return_value = 3  # Wednesday

            # Should complete without raising exception
            run_scheduler(mock_client, mock_storage, config, mode="post", dry_run=True)

            # Verify span.set_attribute was called and second exception was caught (lines 220-221)
            assert mock_span.set_attribute.call_count == 2  # mode (success), dry_run (exception caught)
