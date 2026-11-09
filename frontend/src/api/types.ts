// Mirrors the backend schemas in backend/app/models/. Keep in sync, or generate from
// /api/openapi.json once the API grows.

export type TestCaseKind = "reference" | "testcase";
export type ExpectedResult = "OK" | "NOK";
export type ErrorCategory = "none" | "timing" | "display";
export type TestCaseSource = "seed" | "upload";

export interface TestCase {
  id: string;
  kind: TestCaseKind;
  name: string;
  description: string;
  reference_id: string | null;
  expected_result: ExpectedResult;
  error_type: string;
  category: ErrorCategory;
  is_edge_case: boolean;
  source: TestCaseSource;
  sha256: string;
  created_at: string;
  manipulation: Record<string, unknown> | null;
  video_url: string;
}

export interface ErrorType {
  id: string;
  category: ErrorCategory;
  description: string;
}

export interface TestCaseUpload {
  file: File;
  name: string;
  kind: TestCaseKind;
  expected_result: ExpectedResult;
  error_type: string;
  reference_id?: string;
  is_edge_case: boolean;
  description?: string;
  id?: string;
}
