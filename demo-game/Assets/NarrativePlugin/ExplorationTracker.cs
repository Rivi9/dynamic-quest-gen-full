using System.Collections.Generic;
using AnyRPG;
using UnityEngine;

/// <summary>
/// Samples the player's position every <see cref="sampleInterval"/> seconds and
/// counts unique grid cells visited. Reports the running total to PlayerDataLogger
/// via OnTileExplored(). Grid cell size is configurable — default 5 m matches
/// a typical AnyRPG zone tile.
/// </summary>
public class ExplorationTracker : MonoBehaviour
{
    [SerializeField] private PlayerDataLogger logger;

    [Tooltip("World-space size of one exploration cell (metres).")]
    [SerializeField] private float cellSize = 5f;

    [Tooltip("How often to sample the player position (seconds).")]
    [SerializeField] private float sampleInterval = 2f;

    private readonly HashSet<Vector2Int> _visited = new HashSet<Vector2Int>();
    private SystemGameManager _sgm;
    private float _timer;

    private void Start()
    {
        _sgm = FindObjectOfType<SystemGameManager>();
        if (_sgm == null)
        {
            Debug.LogWarning("[ExplorationTracker] SystemGameManager not found; tracker disabled.");
            enabled = false;
        }
    }

    private void Update()
    {
        _timer += Time.deltaTime;
        if (_timer < sampleInterval) return;
        _timer = 0f;

        var unit = _sgm?.PlayerManager?.ActiveCharacter?.UnitController;
        if (unit == null) return;

        var pos   = unit.transform.position;
        var cell  = new Vector2Int(
            Mathf.FloorToInt(pos.x / cellSize),
            Mathf.FloorToInt(pos.z / cellSize)
        );

        if (_visited.Add(cell))
            logger?.OnTileExplored(_visited.Count);
    }

    /// <summary>Reset the visited set when a new level loads.</summary>
    public void ResetOnLevelLoad()
    {
        _visited.Clear();
    }
}
