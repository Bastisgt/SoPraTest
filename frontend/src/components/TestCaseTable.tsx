import type { TestCase } from "../api/types";

interface Props {
  testCases: TestCase[];
  selectedId: string | null;
  onSelect: (tc: TestCase) => void;
  onDelete: (tc: TestCase) => void;
}

export function TestCaseTable({ testCases, selectedId, onSelect, onDelete }: Props) {
  if (testCases.length === 0) return <p>Keine Testfälle vorhanden.</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Name</th>
          <th>Referenz</th>
          <th>Erwartet</th>
          <th>Fehlerart</th>
          <th>Kategorie</th>
          <th>Quelle</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {testCases.map((tc) => (
          <tr
            key={tc.id}
            className={tc.id === selectedId ? "selected" : undefined}
            onClick={() => onSelect(tc)}
          >
            <td>{tc.id}</td>
            <td>
              {tc.name}
              {tc.is_edge_case && <span className="tag">Grenzfall</span>}
            </td>
            <td>{tc.kind === "reference" ? "–" : tc.reference_id}</td>
            <td className={tc.expected_result === "NOK" ? "nok" : "ok"}>{tc.expected_result}</td>
            <td>{tc.error_type}</td>
            <td>{tc.category}</td>
            <td>{tc.source}</td>
            <td>
              {tc.source === "upload" && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(tc);
                  }}
                >
                  Löschen
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
