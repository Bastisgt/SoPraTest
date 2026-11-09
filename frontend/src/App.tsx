import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type { ErrorType, TestCase } from "./api/types";
import { TestCaseDetail } from "./components/TestCaseDetail";
import { TestCaseTable } from "./components/TestCaseTable";
import { UploadForm } from "./components/UploadForm";

export function App() {
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [errorTypes, setErrorTypes] = useState<ErrorType[]>([]);
  const [selected, setSelected] = useState<TestCase | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const [cases, types] = await Promise.all([api.listTestCases(), api.listErrorTypes()]);
      setTestCases(cases);
      setErrorTypes(types);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function handleDelete(tc: TestCase) {
    if (!confirm(`Testfall ${tc.id} löschen?`)) return;
    try {
      await api.deleteTestCase(tc.id);
      if (selected?.id === tc.id) setSelected(null);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <main>
      <h1>VLM Animation Check</h1>
      <h2>Testfälle &amp; Datensatz</h2>
      {error && <p className="error">{error}</p>}

      <div className="layout">
        <TestCaseTable
          testCases={testCases}
          selectedId={selected?.id ?? null}
          onSelect={setSelected}
          onDelete={handleDelete}
        />
        <aside>
          {selected && <TestCaseDetail testCase={selected} />}
          <UploadForm
            references={testCases.filter((tc) => tc.kind === "reference")}
            errorTypes={errorTypes}
            onUploaded={async (tc) => {
              await reload();
              setSelected(tc);
            }}
          />
        </aside>
      </div>
    </main>
  );
}
