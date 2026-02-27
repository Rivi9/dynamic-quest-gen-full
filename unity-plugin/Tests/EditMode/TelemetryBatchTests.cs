using NUnit.Framework;
using System;

// EditMode tests — no MonoBehaviour, no coroutines needed
public class TelemetryBatchTests
{
    [Test]
    public void TelemetryBatch_DefaultTotalTiles_Is100()
    {
        var batch = new TelemetryBatch();
        Assert.AreEqual(100, batch.total_tiles);
    }

    [Test]
    public void TelemetryBatch_DefaultLocation_IsUnknown()
    {
        var batch = new TelemetryBatch();
        Assert.AreEqual("unknown", batch.current_location);
    }

    [Test]
    public void TelemetryBatch_DefaultObjective_IsNone()
    {
        var batch = new TelemetryBatch();
        Assert.AreEqual("none", batch.current_objective);
    }

    [Test]
    public void TelemetryBatch_FieldsAreSerializable()
    {
        // Verify the [Serializable] attribute allows JsonUtility-style serialization
        var type = typeof(TelemetryBatch);
        Assert.IsTrue(type.IsSerializable,
            "TelemetryBatch must carry [Serializable] for JsonUtility.ToJson");
    }

    [Test]
    public void TelemetryBatch_AllNumericFieldsDefaultToZero()
    {
        var batch = new TelemetryBatch();
        Assert.AreEqual(0, batch.kills);
        Assert.AreEqual(0, batch.deaths);
        Assert.AreEqual(0f, batch.damage_taken, 0.001f);
        Assert.AreEqual(0f, batch.damage_dealt, 0.001f);
        Assert.AreEqual(0, batch.abilities_used);
        Assert.AreEqual(0, batch.abilities_hit);
        Assert.AreEqual(0, batch.objectives_completed);
        Assert.AreEqual(0, batch.objectives_attempted);
    }

    [Test]
    public void TelemetryBatch_WindowTimestamps_AreDoubles()
    {
        var batch = new TelemetryBatch();
        batch.window_start = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
        batch.window_end   = batch.window_start + 5.0;
        Assert.Greater(batch.window_end, batch.window_start);
    }
}
