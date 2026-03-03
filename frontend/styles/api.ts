import { Report } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function searchNews(query: string): Promise<Report> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      cache: "no-store",
    });
  } catch {
    throw new Error(`Cannot reach backend at ${API_BASE}. Ensure FastAPI is running on port 8000.`);
  }

  if (!res.ok) {
    const text = await res.text();
    let detail = "";
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      detail = parsed.detail || "";
    } catch {
      detail = text;
    }
    throw new Error(detail || "Search request failed");
  }

  return (await res.json()) as Report;
}

export async function getReport(id: string): Promise<Report> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/report/${id}`, { cache: "no-store" });
  } catch {
    throw new Error(`Cannot reach backend at ${API_BASE}. Ensure FastAPI is running on port 8000.`);
  }
  if (!res.ok) {
    const text = await res.text();
    let detail = "";
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      detail = parsed.detail || "";
    } catch {
      detail = text;
    }
    throw new Error(detail || "Failed to fetch report");
  }
  return (await res.json()) as Report;
}
