// Thin typed fetch wrapper. Types in ./schema.ts are generated from the FastAPI OpenAPI
// spec (`npm run gen:api`), so frontend and backend contracts cannot drift silently.

export type ApiError = { code: string; message: string; details: unknown };

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiRequestError extends Error {
  constructor(public status: number, public body: ApiError) {
    super(body.message);
  }
}

export async function apiGet<T>(
  path: string,
  params: Record<string, string | number | undefined> = {},
  init?: RequestInit,
): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as ApiError | null;
    throw new ApiRequestError(
      res.status,
      body ?? { code: "NETWORK_ERROR", message: "서버에 연결할 수 없습니다.", details: null },
    );
  }
  return (await res.json()) as T;
}
