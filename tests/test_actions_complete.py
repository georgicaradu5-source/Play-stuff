"""Complete coverage tests for actions.py - all uncovered lines."""

from unittest.mock import MagicMock, patch

from actions import act_on_search, make_post


class TestMakePost:
    """Tests for make_post function to cover line 64 (media handling)."""

    def test_make_post_with_media_enabled(self):
        """Test media handling when allow_media=True (covers line 64)."""
        result = make_post("data-viz", "morning", allow_media=True)

        assert result is not None
        assert len(result) == 2  # (text, media_path)
        # Line 64 `pass` covered when allow_media=True branch entered

    def test_make_post_without_media(self):
        """Test make_post without media (baseline)."""
        result = make_post("power-platform", "afternoon", allow_media=False)

        assert result is not None
        assert len(result) == 2


class TestActOnSearchNonDryRun:
    """Tests for act_on_search in non-dry-run mode (covers API call lines)."""

    @patch("time.sleep")
    @patch("random.uniform", return_value=0.5)
    def test_reply_action_non_dry_run(self, mock_uniform, mock_sleep):
        """Test reply action calls client.create_post (covers lines 121-123)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [
            {"id": "tweet_123", "text": "Interesting Power Platform question", "author_id": "user_456"}
        ]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="Power Platform help",
            limits={"reply": 1, "like": 0, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Verify create_post called with reply
        mock_client.create_post.assert_called_once()
        call_args = mock_client.create_post.call_args
        assert call_args[1].get("reply_to") == "tweet_123"

        # Verify storage logged the action
        mock_storage.log_action.assert_called_once()
        log_call = mock_storage.log_action.call_args
        assert log_call[1]["kind"] == "reply"
        assert log_call[1]["post_id"] == "tweet_123"

        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("random.uniform", return_value=0.5)
    def test_like_action_non_dry_run(self, mock_uniform, mock_sleep):
        """Test like action calls client.like_post (covers lines 132-133)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [
            {"id": "tweet_123", "text": "Great data viz example", "author_id": "user_456"}
        ]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="data visualization",
            limits={"reply": 0, "like": 1, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Verify like_post called
        mock_client.like_post.assert_called_once_with("tweet_123")

        # Verify storage logged the action
        mock_storage.log_action.assert_called_once()
        log_call = mock_storage.log_action.call_args
        assert log_call[1]["kind"] == "like"
        assert log_call[1]["post_id"] == "tweet_123"

        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("random.uniform", return_value=0.5)
    def test_follow_action_non_dry_run(self, mock_uniform, mock_sleep):
        """Test follow action calls client.follow_user (covers lines 142-143)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [
            {"id": "tweet_123", "text": "Helpful Azure content", "author_id": "user_456"}
        ]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="Azure tips",
            limits={"reply": 0, "like": 0, "follow": 1, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Verify follow_user called
        mock_client.follow_user.assert_called_once_with("user_456")

        # Verify storage logged the action
        mock_storage.log_action.assert_called_once()
        log_call = mock_storage.log_action.call_args
        assert log_call[1]["kind"] == "follow"
        assert log_call[1]["post_id"] == "user_456"

        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("random.uniform", return_value=0.5)
    def test_repost_action_non_dry_run(self, mock_uniform, mock_sleep):
        """Test repost action calls client.retweet (covers lines 152-153)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [
            {"id": "tweet_123", "text": "Important automation insight", "author_id": "user_456"}
        ]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="automation",
            limits={"reply": 0, "like": 0, "follow": 0, "repost": 1},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Verify retweet called
        mock_client.retweet.assert_called_once_with("tweet_123")

        # Verify storage logged the action
        mock_storage.log_action.assert_called_once()
        log_call = mock_storage.log_action.call_args
        assert log_call[1]["kind"] == "repost"
        assert log_call[1]["post_id"] == "tweet_123"

        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("random.uniform", return_value=0.5)
    def test_multiple_actions_non_dry_run(self, mock_uniform, mock_sleep):
        """Test multiple action types in single call (integration)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [
            {"id": "tweet_1", "text": "First tweet", "author_id": "user_1"},
            {"id": "tweet_2", "text": "Second tweet", "author_id": "user_2"},
        ]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="Power Platform",
            limits={"reply": 1, "like": 1, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Both actions should be called (order depends on shuffle)
        assert mock_storage.log_action.call_count == 2

    @patch("time.sleep")
    def test_search_api_returns_response(self, mock_sleep):
        """Test search_recent API call returns response (covers line 87)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [{"id": "tweet_1", "text": "Test", "author_id": "user_1"}]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = True
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="test",
            limits={"reply": 1, "like": 0, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Verify search_recent was called (line 87)
        mock_client.search_recent.assert_called_once_with("test", max_results=20)

    @patch("time.sleep")
    def test_skips_self_tweets(self, mock_sleep):
        """Test that own tweets are skipped."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [{"id": "tweet_self", "text": "My own tweet", "author_id": "me_999"}]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="test",
            limits={"reply": 1, "like": 0, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Should not log any action (skipped self tweet)
        mock_storage.log_action.assert_not_called()

    @patch("time.sleep")
    def test_respects_already_acted(self, mock_sleep):
        """Test that already-acted tweets are skipped."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [{"id": "tweet_123", "text": "Already seen", "author_id": "user_456"}]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = True
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="test",
            limits={"reply": 1, "like": 0, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # Should not log action (already acted)
        mock_storage.log_action.assert_not_called()

    def test_dry_run_reply_action(self, capsys):
        """Test dry run mode for reply action specifically (covers line 119)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [{"id": "tweet_1", "text": "Test tweet", "author_id": "user_1"}]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="test",
            limits={"reply": 1, "like": 0, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=True,
            me_user_id="me_999",
        )

        # In dry run mode, no API calls
        mock_client.create_post.assert_not_called()

        # Verify dry run print for reply happened
        captured = capsys.readouterr()
        assert "[DRY RUN] reply to" in captured.out

    def test_zero_quota_skips_action(self):
        """Test that actions with zero quota are skipped (covers line 113)."""
        mock_client = MagicMock()
        mock_client.search_recent.return_value = [{"id": "tweet_1", "text": "Test tweet", "author_id": "user_1"}]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        result = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="test",
            limits={"reply": 0, "like": 0, "follow": 0, "repost": 0},
            jitter_bounds=(1, 2),
            dry_run=False,
            me_user_id="me_999",
        )

        # No actions should be taken with all quotas at zero
        mock_storage.log_action.assert_not_called()
        assert result == {"reply": 0, "like": 0, "follow": 0, "repost": 0}

    @patch("random.shuffle")
    def test_dry_run_mode_all_actions(self, mock_shuffle, capsys):
        """Test dry run mode prints all action types (covers lines 113, 119, 130, 140, 150)."""
        # Don't actually shuffle so test is deterministic
        mock_shuffle.return_value = None  # shuffle modifies in-place

        mock_client = MagicMock()
        mock_client.search_recent.return_value = [
            {"id": "tweet_1", "text": "Test tweet 1", "author_id": "user_1"},
            {"id": "tweet_2", "text": "Test tweet 2", "author_id": "user_2"},
            {"id": "tweet_3", "text": "Test tweet 3", "author_id": "user_3"},
            {"id": "tweet_4", "text": "Test tweet 4", "author_id": "user_4"},
        ]

        mock_storage = MagicMock()
        mock_storage.already_acted.return_value = False
        mock_storage.get_me_user_id.return_value = "me_999"

        _ = act_on_search(
            client=mock_client,
            storage=mock_storage,
            query="test",
            limits={"reply": 1, "like": 1, "follow": 1, "repost": 1},
            jitter_bounds=(1, 2),
            dry_run=True,
            me_user_id="me_999",
        )

        # In dry run mode, no API calls should be made
        mock_client.create_post.assert_not_called()
        mock_client.like_post.assert_not_called()
        mock_client.follow_user.assert_not_called()
        mock_client.retweet.assert_not_called()

        # Verify dry run prints happened
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        assert (
            "reply" in captured.out.lower()
            or "like" in captured.out
            or "follow" in captured.out
            or "repost" in captured.out
        )
