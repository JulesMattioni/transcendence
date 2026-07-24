import { useEffect, useState } from "react";
import { listMyConnections, type Connection } from "../../../api/org";
import { fetchConnectedFriends } from "../../../api/realtime";

/** Best available display name for a connection: full name, email, or id. */
function displayName(c: Connection): string {
  const full = [c.first_name, c.last_name].filter(Boolean).join(" ");
  return full || c.email || `User #${c.user_id}`;
}

/**
 * Panel listing the user's connections (people sharing an organisation)
 * with a live online/offline indicator polled from the realtime service.
 */
function ConnectionsPanel({ myUserId }: { myUserId: number }) {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [onlineIds, setOnlineIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    listMyConnections(myUserId)
      .then((data) => active && setConnections(data))
      .catch(() => active && setConnections([]))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [myUserId]);

  useEffect(() => {
    let active = true;
    const load = () => {
      fetchConnectedFriends(myUserId)
        .then((ids) => active && setOnlineIds(new Set(ids)))
        .catch(() => active && setOnlineIds(new Set()));
    };
    load();
    const interval = setInterval(load, 10000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [myUserId]);

  return (
    <div className="flex h-96 flex-col rounded bg-white shadow-sm">
      <div className="shrink-0 border-b border-gray-200 px-4 py-3">
        <h2 className="font-sans text-lg font-semibold text-black">
          My connections
        </h2>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading ? (
          <p className="px-4 py-3 text-sm text-muted">Loading…</p>
        ) : connections.length === 0 ? (
          <p className="px-4 py-3 text-sm text-muted">No connections yet.</p>
        ) : (
          <ul>
            {connections.map((c) => {
              const online = onlineIds.has(c.user_id);
              return (
                <li
                  key={c.user_id}
                  className="flex items-center gap-3 px-4 py-3"
                >
                  <span
                    className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                      online ? "bg-green-500" : "bg-gray-300"
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-black">
                      {displayName(c)}
                    </p>
                    {c.email && (
                      <p className="truncate text-xs text-muted">{c.email}</p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ConnectionsPanel;
