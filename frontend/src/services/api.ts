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
  previous_creditor_name: string | null;
  amount: string | null;
  currency: string;
  claim_reference: string | null;
  contract_reference: string | null;
  contact_name: string | null;
  contact_organization: string | null;
  contact_person: string | null;
  street: string | null;
  postal_code: string | null;
  city: string | null;
  country: string | null;
  email: string | null;
  phone: string | null;
  title_exists: boolean;
  title_type: string | null;
  status: string;
  event_type: string;
  event_date: string | null;
  transfer_date: string | null;
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

export type ClaimRead = {
  id: number;
  amount: string | null;
  currency: string;
  claim_reference: string | null;
  contract_reference: string | null;
  title_exists: boolean;
  title_type: string | null;
  status: string;
  first_seen: string | null;
  last_seen: string | null;
};

export type CreditorSummary = {
  id: number;
  canonical_name: string;
  active: boolean;
  claim_count: number;
  total_amount: string;
  open_amount: string;
};

export type ContactSummary = {
  id: number;
  display_name: string;
  organization_name: string | null;
  person_name: string | null;
  street: string | null;
  postal_code: string | null;
  city: string | null;
  country: string;
  email: string | null;
  phone: string | null;
  document_count: number;
  creditor_count: number;
  created_at: string;
  updated_at: string;
};

export type ClaimTransferRead = {
  id: number;
  claim_id: number;
  claim_reference: string | null;
  contract_reference: string | null;
  from_creditor_id: number | null;
  from_creditor_name: string | null;
  to_creditor_id: number | null;
  to_creditor_name: string | null;
  document_id: number | null;
  document_filename: string | null;
  transfer_date: string | null;
  notes: string | null;
  created_at: string;
};

export type DashboardSummary = {
  document_count: number;
  creditor_count: number;
  claim_count: number;
  total_claim_amount: string;
  open_claim_amount: string;
  titled_claim_count: number;
  status_buckets: { status: string; count: number; amount: string }[];
};

export type ChatResponse = {
  answer: string;
  provider: string;
  model: string;
  sources: { document_id: number; filename: string; snippet: string }[];
};

export type ComparisonGroup = {
  reason: string;
  items: {
    claim_id: number;
    creditor: string | null;
    amount: string | null;
    currency: string;
    claim_reference: string | null;
    contract_reference: string | null;
    status: string;
  }[];
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

export async function fetchDashboard(): Promise<DashboardSummary> {
  const response = await api.get<DashboardSummary>("/api/dashboard");
  return response.data;
}

export async function fetchCreditors(): Promise<CreditorSummary[]> {
  const response = await api.get<CreditorSummary[]>("/api/creditors");
  return response.data;
}

export async function fetchContacts(): Promise<ContactSummary[]> {
  const response = await api.get<ContactSummary[]>("/api/contacts");
  return response.data;
}

export async function fetchTransfers(): Promise<ClaimTransferRead[]> {
  const response = await api.get<ClaimTransferRead[]>("/api/transfers");
  return response.data;
}

export async function askChat(question: string): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/api/chat", { question });
  return response.data;
}

export function exportClaimsUrl(): string {
  return `${baseURL}/api/exports/claims.csv`;
}

export async function fetchComparisons(): Promise<ComparisonGroup[]> {
  const response = await api.get<ComparisonGroup[]>("/api/comparisons/claims");
  return response.data;
}
