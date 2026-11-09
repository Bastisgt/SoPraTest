import type { TestCase } from "../api/types";

export function TestCaseDetail({ testCase }: { testCase: TestCase }) {
  return (
    <section className="card">
      <h2>
        {testCase.id}: {testCase.name}
      </h2>
      {/* key forces a reload when switching between test cases */}
      <video key={testCase.id} src={testCase.video_url} controls loop muted />
      {testCase.description && <p>{testCase.description}</p>}
      {testCase.manipulation && (
        <p>
          Manipulation: <code>{JSON.stringify(testCase.manipulation)}</code>
        </p>
      )}
      <p className="muted">SHA-256: {testCase.sha256}</p>
    </section>
  );
}
