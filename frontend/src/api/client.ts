import type { ErrorType, TestCase, TestCaseUpload } from "./types";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

// FastAPI returns errors as {"detail": string | string[] | object[]}.
function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (typeof d === "string" ? d : (d?.msg ?? JSON.stringify(d)))).join("; ");
  }
  return JSON.stringify(detail);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.detail ? formatDetail(body.detail) : res.statusText);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const api = {
  listTestCases: () => request<TestCase[]>("/api/testcases"),

  listErrorTypes: () => request<ErrorType[]>("/api/error-types"),

  uploadTestCase: (data: TestCaseUpload) => {
    const form = new FormData();
    for (const [key, value] of Object.entries(data)) {
      if (value === undefined || value === "") continue;
      form.append(key, value instanceof File ? value : String(value));
    }
    return request<TestCase>("/api/testcases", { method: "POST", body: form });
  },

  deleteTestCase: (id: string) =>
    request<void>(`/api/testcases/${encodeURIComponent(id)}`, { method: "DELETE" }),
};
