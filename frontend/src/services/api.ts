import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL,
});

export type DocumentSummary = {
  id: number;
  paperless_id: number;
  filename: string;
  created_at: string | null;
  document_date: string | null;
  document_type: string | null;
  checksum: string | null;
  confidence_score: string | null;
  paperless_url: string | null;
  imported_at: string;
  updated_at: string;
};

export type DocumentDetail = DocumentSummary & {
  ocr_text: string | null;
};

export type DocumentListResponse = {
  items: DocumentSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type ImportResult = {
  imported: number;
  created: number;
  updated: number;
  skipped: number;
};

export async function fetchDocuments(search: string): Promise<DocumentListResponse> {
  const response = await api.get<DocumentListResponse>("/api/documents", {
    params: search ? { search } : undefined,
  });
  return response.data;
}

export async function fetchDocument(id: number): Promise<DocumentDetail> {
  const response = await api.get<DocumentDetail>(`/api/documents/${id}`);
  return response.data;
}

export async function importPaperless(): Promise<ImportResult> {
  const response = await api.post<ImportResult>("/api/import/paperless", {});
  return response.data;
}
