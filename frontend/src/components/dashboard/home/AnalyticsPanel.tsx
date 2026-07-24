import { useCallback, useEffect, useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Download, FileText, HardDrive, Layers } from "lucide-react";
import { getFileStats, type FileStats } from "../../../api/files";

const CATEGORY_COLORS: Record<string, string> = {
  image: "#ff7b00",
  pdf: "#df0000",
  document: "#006AFF",
  spreadsheet: "#00f50c",
  video: "#9b31ff",
  audio: "#00f7ff",
  archive: "#f50072",
  other: "#64748B",
};

const CATEGORY_LABELS: Record<string, string> = {
  image: "Images",
  pdf: "PDF",
  document: "Documents",
  spreadsheet: "Spreadsheets",
  video: "Video",
  audio: "Audio",
  archive: "Archives",
  other: "Other",
};

const PRESETS = [
  { label: "Today", hours: null, sinceMidnight: true },
  { label: "Last 6h", hours: 6, sinceMidnight: false },
  { label: "Last 24h", hours: 24, sinceMidnight: false },
  { label: "All time", hours: null, sinceMidnight: false },
] as const;

const POLL_INTERVAL_MS = 10000;

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const exp = Math.min(
    units.length - 1,
    Math.floor(Math.log(bytes) / Math.log(1024)),
  );
  const value = bytes / Math.pow(1024, exp);
  return `${value.toFixed(value >= 10 || exp === 0 ? 0 : 1)} ${units[exp]}`;
}

function formatBucket(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}

function categoryColor(category: string): string {
  return CATEGORY_COLORS[category] ?? CATEGORY_COLORS.other;
}

function startForPreset(preset: (typeof PRESETS)[number]): string | undefined {
  if (preset.sinceMidnight) {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d.toISOString();
  }
  if (preset.hours === null) return undefined; // "All time"
  const d = new Date();
  d.setHours(d.getHours() - preset.hours);
  return d.toISOString();
}

function AnalyticsPanel({ orgId }: { orgId: number }) {
  const [stats, setStats] = useState<FileStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [presetIndex, setPresetIndex] = useState(0);

  const load = useCallback(() => {
    const start = startForPreset(PRESETS[presetIndex]);
    return getFileStats(orgId, start)
      .then((data) => {
        setStats(data);
        setError(null);
      })
      .catch(() => setError("Could not load analytics."))
      .finally(() => setLoading(false));
  }, [orgId, presetIndex]);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [load]);

  const pieData = useMemo(
    () =>
      (stats?.by_type ?? []).map((t) => ({
        key: t.category,
        name: categoryLabel(t.category),
        value: t.file_count,
        bytes: t.total_bytes,
      })),
    [stats],
  );

  const lineData = useMemo(
    () =>
      (stats?.by_bucket ?? []).map((b) => ({
        time: formatBucket(b.bucket_start),
        uploads: b.file_count,
      })),
    [stats],
  );

  const isEmpty = !loading && (stats?.total_files ?? 0) === 0;

  function handleExportCsv() {
    if (!stats) return;
    const rows: string[] = ["metric,category,file_count,total_bytes"];
    rows.push(`total,,${stats.total_files},${stats.total_bytes}`);
    for (const t of stats.by_type) {
      rows.push(
        `by_type,${categoryLabel(t.category)},${t.file_count},${t.total_bytes}`,
      );
    }
    for (const b of stats.by_bucket) {
      rows.push(`by_bucket,${b.bucket_start},${b.file_count},`);
    }
    const csv = rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `analytics-org-${orgId}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="mt-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-serif text-xl font-bold text-black">Analytics</h2>
        <div className="flex flex-wrap items-center gap-2">
          {/* Date range presets */}
          <div className="flex items-center gap-1 rounded bg-white p-1 shadow-sm">
            {PRESETS.map((preset, i) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => {
                  if (i === presetIndex) return;
                  setLoading(true);
                  setPresetIndex(i);
                }}
                className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                  i === presetIndex
                    ? "bg-keepr text-white"
                    : "text-muted hover:bg-gray-100"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={!stats || isEmpty}
            className="inline-flex items-center gap-1.5 rounded border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-muted shadow-sm transition-colors hover:bg-gray-50 hover:text-black disabled:opacity-50"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {/* KPI tiles */}
      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiTile
          icon={<FileText size={18} />}
          label="Total files"
          value={stats ? String(stats.total_files) : "—"}
        />
        <KpiTile
          icon={<HardDrive size={18} />}
          label="Storage used"
          value={stats ? formatBytes(stats.total_bytes) : "—"}
        />
        <KpiTile
          icon={<Layers size={18} />}
          label="File types"
          value={stats ? String(stats.by_type.length) : "—"}
        />
      </div>

      {isEmpty ? (
        <div className="mt-4 rounded bg-white p-10 text-center shadow-sm">
          <p className="text-sm text-muted">
            No files in this range yet. Upload files to see analytics.
          </p>
        </div>
      ) : (
        <div
          className={`mt-4 grid grid-cols-1 gap-4 transition-opacity lg:grid-cols-2 ${
            loading ? "opacity-60" : "opacity-100"
          }`}
        >
          {/* Pie — files by type */}
          <div className="rounded bg-white p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-black">Files by type</h3>
            <div className="mt-2 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={2}
                    stroke="#ffffff"
                    strokeWidth={2}
                  >
                    {pieData.map((entry) => (
                      <Cell key={entry.key} fill={categoryColor(entry.key)} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, _name, item) => {
                      const count = Number(value);
                      const bytes = item?.payload?.bytes as number | undefined;
                      const suffix =
                        bytes != null ? ` · ${formatBytes(bytes)}` : "";
                      return [
                        `${count} file${count > 1 ? "s" : ""}${suffix}`,
                        "",
                      ];
                    }}
                    contentStyle={{
                      borderRadius: 4,
                      border: "1px solid #e5e7eb",
                      fontSize: 12,
                    }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Line — uploads over time */}
          <div className="rounded bg-white p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-black">
              Uploads over time
            </h3>
            <div className="mt-2 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={lineData}
                  margin={{ top: 8, right: 12, bottom: 4, left: -18 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#f0f0f0"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 12, fill: "#585858" }}
                    tickLine={false}
                    axisLine={{ stroke: "#e5e7eb" }}
                    minTickGap={24}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 12, fill: "#585858" }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    formatter={(value) => {
                      const count = Number(value);
                      return [`${count} upload${count > 1 ? "s" : ""}`, ""];
                    }}
                    contentStyle={{
                      borderRadius: 4,
                      border: "1px solid #e5e7eb",
                      fontSize: 12,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="uploads"
                    stroke="#006AFF"
                    strokeWidth={2}
                    dot={
                      lineData.length <= 48
                        ? { r: 3, fill: "#006AFF" }
                        : false
                    }
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function KpiTile({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded bg-white p-4 shadow-sm">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-blue-50 text-keepr">
        {icon}
      </span>
      <div className="min-w-0">
        <p className="text-xs text-muted">{label}</p>
        <p className="truncate text-xl font-bold text-black">{value}</p>
      </div>
    </div>
  );
}

export default AnalyticsPanel;
