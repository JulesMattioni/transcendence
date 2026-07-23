import { useEffect, useState } from "react";
import { listMyConnections, type Connection } from "../../../api/org";

function displayName(c: Connection): string {
  const full = [c.first_name, c.last_name].filter(Boolean).join(" ");
  return full || c.email || `User #${c.user_id}`;
}

// Mock online status.
function mockOnline(userId: number): boolean {
  return userId % 2 === 0;
}

function ConnectionsPanel({ myUserId }: { myUserId: number }) {
  const [connections, setConnections] = useState<Connection[]>([]);
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

  return (
    <div className="border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="font-sans text-lg font-semibold text-black">
          My connections
        </h2>
      </div>
      {loading ? (
        <p className="px-4 py-3 text-sm text-muted">Loading…</p>
      ) : connections.length === 0 ? (
        <p className="px-4 py-3 text-sm text-muted">No connections yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200">
          {connections.map((c) => {
            const online = mockOnline(c.user_id);
            return (
              <li key={c.user_id} className="flex items-center gap-3 px-4 py-3">
                <span
                  className={`h-2.5 w-2.5 shrink-0 rounded-full ${
                    online ? "bg-green-500" : "bg-gray-300"
                  }`}
                  aria-label={online ? "online" : "offline"}
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
  );
}

export default ConnectionsPanel;
