"""Coverage tests for remaining uncovered lines in scheduler.py."""

from unittest.mock import MagicMock, patch

from scheduler import run_interact_actions, run_post_action, run_scheduler


class TestRunPostActionDuplicateDetection:
    """Tests for duplicate detection in run_post_action."""

    @patch("scheduler.choose_template")
    @patch("scheduler.start_span")
    def test_duplicate_text_detected(self, mock_span, mock_template):
        """Test duplicate text detection skips post (covers lines 89-92)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_storage.is_text_duplicate.return_value = True  # Simulate duplicate

        config = {
            "schedule": {"windows": ["morning"]},
            "topics": ["AI"],
            "learning": {"enabled": False},
        }

        mock_template.return_value = "Duplicate text"

        # Mock span context
        mock_span_obj = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span_obj)
        mock_span.__exit__ = MagicMock(return_value=False)

        # Execute
        run_post_action(mock_client, mock_storage, config, dry_run=False)

        # Verify duplicate check was called
        assert mock_storage.is_text_duplicate.called
        # Verify post was NOT created
        assert not mock_client.create_post.called

    @patch("scheduler.choose_template")
    @patch("scheduler.start_span")
    def test_span_set_attribute_exception_handled(self, mock_span, mock_template):
        """Test exception handling for span.set_attribute (covers lines 80-81)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_storage.is_text_duplicate.return_value = False

        config = {
            "schedule": {"windows": ["morning"]},
            "topics": ["AI"],
            "learning": {"enabled": False},
        }

        mock_template.return_value = "Test post"

        # Mock span that raises exception on set_attribute
        mock_span_obj = MagicMock()
        mock_span_obj.set_attribute.side_effect = Exception("Span error")
        mock_span.__enter__ = MagicMock(return_value=mock_span_obj)
        mock_span.__exit__ = MagicMock(return_value=False)

        # Execute - should not raise exception despite span errors
        run_post_action(mock_client, mock_storage, config, dry_run=True)
        # If we get here without exception, the test passes


class TestRunInteractActionsEdgeCases:
    """Tests for edge cases in run_interact_actions."""

    @patch("scheduler.act_on_search")
    @patch("scheduler.start_span")
    def test_empty_query_skipped(self, mock_span, mock_act):
        """Test empty query strings are skipped (covers line 184)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()

        config = {
            "queries": [
                {"query": "valid query"},
                {"query": ""},  # Empty query - should be skipped
                {"query": "another valid"},
            ]
        }

        # Mock span context
        mock_span_obj = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span_obj)
        mock_span.__exit__ = MagicMock(return_value=False)

        mock_act.return_value = 5  # Remaining actions

        # Execute
        run_interact_actions(mock_client, mock_storage, config, dry_run=True)

        # Verify act_on_search called only twice (empty query skipped)
        assert mock_act.call_count == 2

    @patch("scheduler.act_on_search")
    @patch("scheduler.start_span")
    def test_query_span_attribute_exception(self, mock_span, mock_act):
        """Test exception handling for query span attributes (covers lines 189-190)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()

        config = {"queries": [{"query": "test query"}]}

        # Mock span that raises exception on set_attribute
        mock_span_obj = MagicMock()
        mock_span_obj.set_attribute.side_effect = Exception("Span error")
        mock_span.__enter__ = MagicMock(return_value=mock_span_obj)
        mock_span.__exit__ = MagicMock(return_value=False)

        mock_act.return_value = 0

        # Execute - should not raise exception
        run_interact_actions(mock_client, mock_storage, config, dry_run=True)

        # Verify execution continued despite span errors
        assert mock_act.called

    @patch("scheduler.act_on_search")
    @patch("scheduler.start_span")
    def test_main_span_exception_handling(self, mock_span, mock_act):
        """Test exception handling for main span attributes (covers lines 173-174)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()

        config = {"queries": [{"query": "test"}]}

        # Mock outer span that raises on set_attribute
        mock_outer_span = MagicMock()
        mock_outer_span.set_attribute.side_effect = Exception("Outer span error")

        # Mock inner span (for query)
        mock_inner_span = MagicMock()

        # Configure context managers
        mock_span.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=mock_outer_span), __exit__=MagicMock(return_value=False)),
            MagicMock(__enter__=MagicMock(return_value=mock_inner_span), __exit__=MagicMock(return_value=False)),
        ]

        mock_act.return_value = 0

        # Execute - should not raise exception
        run_interact_actions(mock_client, mock_storage, config, dry_run=True)

        # Verify execution continued
        assert mock_act.called
class TestRunSchedulerEdgeCases:
    """Tests for edge cases in run_scheduler."""

    @patch("scheduler.run_interact_actions")
    @patch("scheduler.run_post_action")
    @patch("scheduler.start_span")
    def test_outside_weekdays_exits(self, mock_span, mock_post, mock_interact):
        """Test scheduler exits when outside configured weekdays (covers lines 223-224)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()

        config = {"cadence": {"weekdays": [1, 2, 3, 4, 5]}}  # Monday-Friday

        # Mock span context
        mock_span_obj = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span_obj)
        mock_span.__exit__ = MagicMock(return_value=False)

        # Execute on a Saturday (day 6)
        with patch("scheduler.datetime") as mock_dt:
            mock_dt.today.return_value.isoweekday.return_value = 6  # Saturday
            mock_dt.now.return_value.strftime.return_value = "2025-11-08 10:00:00"

            run_scheduler(mock_client, mock_storage, config, "both", dry_run=False)

        # Verify neither post nor interact was called
        assert not mock_post.called
        assert not mock_interact.called

    @patch("scheduler.run_interact_actions")
    @patch("scheduler.run_post_action")
    @patch("scheduler.start_span")
    def test_scheduler_span_exception_handling(self, mock_span, mock_post, mock_interact):
        """Test exception handling for scheduler span attributes (covers lines 220-221)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()

        config = {"cadence": {"weekdays": [1, 2, 3, 4, 5, 6, 7]}}  # All days

        # Mock span that raises exception on set_attribute
        mock_span_obj = MagicMock()
        mock_span_obj.set_attribute.side_effect = Exception("Span error")
        mock_span.__enter__ = MagicMock(return_value=mock_span_obj)
        mock_span.__exit__ = MagicMock(return_value=False)

        # Execute - should not raise exception
        run_scheduler(mock_client, mock_storage, config, "post", dry_run=True)

        # Verify execution continued despite span errors
        assert mock_post.called

    @patch("scheduler.run_interact_actions")
    @patch("scheduler.run_post_action")
    @patch("scheduler.start_span")
    def test_scheduler_completion_message(self, mock_span, mock_post, mock_interact):
        """Test scheduler prints completion message (covers line 238)."""
        # Setup
        mock_client = MagicMock()
        mock_storage = MagicMock()

        config = {"cadence": {"weekdays": [1, 2, 3, 4, 5, 6, 7]}}

        # Mock span context
        mock_span_obj = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span_obj)
        mock_span.__exit__ = MagicMock(return_value=False)

        # Execute with capsys to capture print output
        with patch("builtins.print") as mock_print:
            run_scheduler(mock_client, mock_storage, config, "both", dry_run=True)

            # Verify completion message was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            completion_printed = any("[OK] Scheduler completed" in str(call) for call in print_calls)
            assert completion_printed