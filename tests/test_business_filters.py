"""Tests for business logic filtering."""


from business.filters import filter_eligible_actions, should_act_on_post


def test_should_act_on_post_not_self():
    """Test that non-self posts are allowed."""
    result = should_act_on_post(
        post_id="12345",
        author_id="author_user_id",
        me_user_id="my_user_id",
    )
    assert result is True


def test_should_act_on_post_self_post():
    """Test that self posts are filtered out."""
    user_id = "same_user_id"
    result = should_act_on_post(
        post_id="67890",
        author_id=user_id,
        me_user_id=user_id,
    )
    assert result is False


def test_should_act_on_post_author_none():
    """Test posts with no author_id are allowed."""
    result = should_act_on_post(
        post_id="99999",
        author_id=None,
        me_user_id="my_user_id",
    )
    assert result is True


def test_should_act_on_post_str_conversion():
    """Test that string conversion handles matching IDs."""
    # Test with different types but same value
    result = should_act_on_post(
        post_id="123",
        author_id=12345,  # int
        me_user_id="12345",  # str
    )
    assert result is False  # Should match after str conversion


def test_filter_eligible_actions_all_have_quota():
    """Test filtering when all actions have quota."""
    available = ["reply", "like", "follow"]
    quotas = {"reply": 5, "like": 10, "follow": 3}

    result = filter_eligible_actions("post123", available, quotas)

    assert set(result) == set(available)


def test_filter_eligible_actions_some_exhausted():
    """Test filtering when some actions have no quota."""
    available = ["reply", "like", "follow", "repost"]
    quotas = {"reply": 0, "like": 5, "follow": 0, "repost": 2}

    result = filter_eligible_actions("post123", available, quotas)

    assert set(result) == {"like", "repost"}


def test_filter_eligible_actions_all_exhausted():
    """Test filtering when all quotas are exhausted."""
    available = ["reply", "like", "follow"]
    quotas = {"reply": 0, "like": 0, "follow": 0}

    result = filter_eligible_actions("post123", available, quotas)

    assert result == []


def test_filter_eligible_actions_empty_available():
    """Test filtering with no available actions."""
    available = []
    quotas = {"reply": 5, "like": 10}

    result = filter_eligible_actions("post123", available, quotas)

    assert result == []


def test_filter_eligible_actions_missing_quota_keys():
    """Test filtering when quota dict is missing some keys."""
    available = ["reply", "like", "follow"]
    quotas = {"reply": 5}  # Missing 'like' and 'follow'

    result = filter_eligible_actions("post123", available, quotas)

    # Only 'reply' has quota, others default to 0
    assert result == ["reply"]


def test_filter_eligible_actions_negative_quota():
    """Test that negative quotas are treated as 0."""
    available = ["reply", "like"]
    quotas = {"reply": -1, "like": 5}

    result = filter_eligible_actions("post123", available, quotas)

    assert result == ["like"]


def test_filter_eligible_actions_preserves_order():
    """Test that output order matches input order."""
    available = ["follow", "reply", "like", "repost"]
    quotas = {"reply": 1, "like": 1, "follow": 1, "repost": 1}

    result = filter_eligible_actions("post123", available, quotas)

    # All have quota, so order should be preserved
    assert result == available


def test_should_act_on_post_edge_case_empty_strings():
    """Test handling of empty string IDs."""
    result = should_act_on_post(
        post_id="",
        author_id="",
        me_user_id="",
    )
    # Empty strings match, but author_id is empty so no self-filter triggered
    assert result is True


def test_should_act_on_post_numeric_ids():
    """Test handling of numeric IDs."""
    result = should_act_on_post(
        post_id="123",
        author_id=999,
        me_user_id=999,
    )
    assert result is False  # Should match after str conversion
