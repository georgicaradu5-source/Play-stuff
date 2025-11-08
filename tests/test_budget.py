from src.budget import BudgetManager  # ruff: noqa: I001


class DummyStorage:
    def __init__(self, read_count=0, create_count=0):
        self._usage = {"read_count": read_count, "create_count": create_count}
        self._updated = {}

    def get_monthly_usage(self, period):
        return self._usage.copy()

    def update_monthly_usage(self, period, read_count=None, create_count=None):
        if read_count is not None:
            self._updated["read_count"] = read_count
        if create_count is not None:
            self._updated["create_count"] = create_count


def test_plan_caps_and_buffer():
    bm = BudgetManager(storage=None, plan="basic", buffer_pct=0.1)
    assert bm.read_cap == 15000
    assert bm.write_cap == 50000
    assert bm.soft_read_cap == int(15000 * 0.9)
    assert bm.soft_write_cap == int(50000 * 0.9)


def test_get_usage_with_storage():
    storage = DummyStorage(read_count=10, create_count=5)
    bm = BudgetManager(storage=storage, plan="free")
    usage = bm.get_usage()
    assert usage["reads"] == 10
    assert usage["writes"] == 5
    assert usage["read_cap"] == 100
    assert usage["write_cap"] == 500


def test_can_read_and_write_caps():
    storage = DummyStorage(read_count=95, create_count=495)
    bm = BudgetManager(storage=storage, plan="free", buffer_pct=0.05)
    # Hard cap exceeded
    ok, msg = bm.can_read(10)
    assert not ok and "Hard cap" in msg
    ok, msg = bm.can_write(10)
    assert not ok and "Hard cap" in msg
    # Soft cap exceeded
    ok, msg = bm.can_read(4)
    assert not ok and "Soft cap" in msg
    ok, msg = bm.can_write(4)
    assert not ok and "Soft cap" in msg
    # At soft cap, should fail (current logic enforces soft cap as limit)
    ok, msg = bm.can_read(1)
    assert not ok and "Soft cap" in msg
    ok, msg = bm.can_write(1)
    assert not ok and "Soft cap" in msg


def test_add_reads_and_writes():
    storage = DummyStorage()
    bm = BudgetManager(storage=storage)
    bm.add_reads(7)
    assert storage._updated["read_count"] == 7
    bm.add_writes(3)
    assert storage._updated["create_count"] == 3


def test_from_config():
    config = {"plan": "pro", "buffer_pct": 0.2, "custom_read_cap": 123, "custom_write_cap": 456}
    bm = BudgetManager.from_config(config)
    assert bm.plan == "pro"
    assert bm.buffer_pct == 0.2
    assert bm.read_cap == 123
    assert bm.write_cap == 456
