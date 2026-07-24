import { useEffect, useState } from "react";
import { subscribeRealtime } from "../../../api/realtime";
import type { RealtimeEvent } from "../../../api/realtime";

function formatEvent(event: RealtimeEvent): string {
  const name =
    [event.first_name, event.last_name].filter(Boolean).join(" ") || "Someone";
  switch (event.event_type) {
    case "auth.login":
      return `${name} logged in`;
    case "auth.logout":
      return `${name} logged out`;
    case "file.created":
      return `${event.file_name} was uploaded to ${event.org_name}`;
    case "file.updated":
      return `${event.file_name} was updated in ${event.org_name}`;
    case "file.deleted":
      return `${event.file_name} was deleted from ${event.org_name}`;
    default:
      return "Unknown activity";
  }
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function AuditPanel() {
  const [events, setEvents] = useState<RealtimeEvent[]>([]);

  useEffect(() => subscribeRealtime(setEvents), []);

  return (
    <div className="flex min-h-0 flex-1 flex-col rounded bg-white shadow-sm">
      <div className="shrink-0 border-b border-gray-200 px-4 py-3">
        <h2 className="font-sans text-lg font-semibold text-black">
          Audit feed
        </h2>
      </div>
      {events.length === 0 ? (
        <p className="px-4 py-6 text-sm text-subtle">No activity yet.</p>
      ) : (
        <ul className="min-h-0 flex-1 overflow-y-auto">
          {events.map((e) => (
            <li key={e.event_id} className="px-4 py-3">
              <p className="text-sm text-muted">{formatEvent(e)}</p>
              <p className="text-xs text-subtle">{formatTime(e.timestamp)}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default AuditPanel;
