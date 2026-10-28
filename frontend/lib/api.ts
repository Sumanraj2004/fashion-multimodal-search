import type {
  CategoriesResponse,
  ImageSearchOptions,
  Product,
  SearchOptions,
  SearchResponse,
} from "@/lib/types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

export class ApiError extends Error {
  readonly status: number;
  readonly retryAfter: string | null;

  constructor(message: string, status: number, retryAfter: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Could not connect to the search API.";
    throw new ApiError(message, 0);
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body: unknown = await response.json();
      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        typeof body.detail === "string"
      ) {
        message = body.detail;
      }
    } catch {
      // Keep the HTTP status message when the response is not JSON.
    }
    throw new ApiError(message, response.status, response.headers.get("Retry-After"));
  }

  return (await response.json()) as T;
}

export function searchText(options: SearchOptions): Promise<SearchResponse> {
  return request<SearchResponse>("/search/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: options.query,
      top_k: options.top_k ?? 12,
      page: options.page ?? 1,
      category: options.category || null,
    }),
  });
}

export function searchImage(options: ImageSearchOptions): Promise<SearchResponse> {
  const form = new FormData();
  form.set("file", options.file);
  form.set("top_k", String(options.top_k ?? 12));
  form.set("page", String(options.page ?? 1));
  if (options.category) form.set("category", options.category);

  return request<SearchResponse>("/search/image", {
    method: "POST",
    body: form,
  });
}

export function getCategories(): Promise<CategoriesResponse> {
  return request<CategoriesResponse>("/categories");
}

export function getProduct(id: string): Promise<Product> {
  return request<Product>(`/products/${encodeURIComponent(id)}`);
}
