const MOCK_AUDIT = [
  { id: 1, text: "Alice uploaded contract.pdf", at: "2 min ago" },
  { id: 2, text: "Bob was added to Org test 1", at: "1 h ago" },
  { id: 3, text: "Charlie deleted report.xlsx", at: "3 h ago" },
];

function AuditPanel() {
  return (
    <div className="border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-4 py-3">
        <h2 className="font-sans text-lg font-semibold text-black">
          Audit feed
        </h2>
      </div>
      <ul>
        {MOCK_AUDIT.map((e) => (
          <li key={e.id} className="px-4 py-3">
            <p className="text-sm text-muted">{e.text}</p>
            <p className="text-xs text-subtle">{e.at}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default AuditPanel;
