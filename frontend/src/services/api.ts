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

export type AIStatus = {
  configured_provider: string;
  available_providers: string[];
};

export type ExtractedClaim = {
  creditor_name: string | null;
  amount: string | null;
  currency: string;
  claim_reference: string | null;
  contract_reference: string | null;
  title_exists: boolean;
  title_type: string | null;
  status: string;
  event_type: string;
  event_date: string | null;
  notes: string | null;
};

export type ClaimExtractionResult = {
  document_id: number;
  claim_id: number;
  creditor_id: number | null;
  provider: string;
  model: string;
  extracted: ExtractedClaim;
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

export async function fetchAIStatus(): Promise<AIStatus> {
  const response = await api.get<AIStatus>("/api/ai/status");
  return response.data;
}

export async function extractClaim(documentId: number): Promise<ClaimExtractionResult> {
  const response = await api.post<ClaimExtractionResult>(`/api/extractions/documents/${documentId}/claim`, {});
  return response.data;
}
