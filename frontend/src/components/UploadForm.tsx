import { useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { ErrorType, ExpectedResult, TestCase, TestCaseKind } from "../api/types";

interface Props {
  references: TestCase[];
  errorTypes: ErrorType[];
  onUploaded: (tc: TestCase) => void;
}

// Upload of a clip as new test case or reference (DS-07).
export function UploadForm({ references, errorTypes, onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [id, setId] = useState("");
  const [kind, setKind] = useState<TestCaseKind>("testcase");
  const [referenceId, setReferenceId] = useState("");
  const [expected, setExpected] = useState<ExpectedResult>("NOK");
  const [errorType, setErrorType] = useState("none");
  const [isEdgeCase, setIsEdgeCase] = useState(false);
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isReference = kind === "reference";

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) return;
    const form = e.currentTarget; // currentTarget is null after the await below
    setBusy(true);
    setError(null);
    try {
      const created = await api.uploadTestCase({
        file,
        name,
        id,
        kind,
        description,
        is_edge_case: isEdgeCase,
        // A reference is by definition correct and links to nothing.
        reference_id: isReference ? undefined : referenceId || references[0]?.id,
        expected_result: isReference ? "OK" : expected,
        error_type: isReference ? "none" : errorType,
      });
      form.reset(); // clears the file input
      setFile(null);
      setName("");
      setId("");
      setDescription("");
      onUploaded(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card upload" onSubmit={submit}>
      <h2>Clip hochladen</h2>

      <label>
        Video
        <input
          type="file"
          accept="video/*"
          required
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </label>
      <label>
        Name
        <input value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label>
        ID (optional)
        <input value={id} onChange={(e) => setId(e.target.value)} placeholder="automatisch: UP-###" />
      </label>
      <label>
        Art
        <select value={kind} onChange={(e) => setKind(e.target.value as TestCaseKind)}>
          <option value="testcase">Testfall</option>
          <option value="reference">Referenz</option>
        </select>
      </label>

      {!isReference && (
        <>
          <label>
            Referenz
            <select value={referenceId} onChange={(e) => setReferenceId(e.target.value)}>
              {references.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.id}: {r.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Erwartetes Ergebnis
            <select value={expected} onChange={(e) => setExpected(e.target.value as ExpectedResult)}>
              <option value="NOK">NOK</option>
              <option value="OK">OK</option>
            </select>
          </label>
          <label>
            Fehlerart
            <select value={errorType} onChange={(e) => setErrorType(e.target.value)}>
              {errorTypes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id} ({t.category}): {t.description}
                </option>
              ))}
            </select>
          </label>
        </>
      )}

      <label className="inline">
        <input type="checkbox" checked={isEdgeCase} onChange={(e) => setIsEdgeCase(e.target.checked)} />
        Grenzfall
      </label>
      <label>
        Beschreibung
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
      </label>

      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={busy || !file}>
        {busy ? "Lädt hoch…" : "Hochladen"}
      </button>
    </form>
  );
}
