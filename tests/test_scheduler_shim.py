def test_scheduler_shim_exports():
    # Ensure legacy import path still works
    import scheduler

    assert hasattr(scheduler, "run_scheduler")
    assert hasattr(scheduler, "run_post_action")
    assert hasattr(scheduler, "run_interact_actions")
    assert hasattr(scheduler, "current_slot")
