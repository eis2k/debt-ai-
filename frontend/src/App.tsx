import DownloadIcon from "@mui/icons-material/Download";
import CancelIcon from "@mui/icons-material/Cancel";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
import SettingsIcon from "@mui/icons-material/Settings";
import SyncIcon from "@mui/icons-material/Sync";
import {
  Alert,
  AppBar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  InputAdornment,
  MenuItem,
  Paper,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import {
  AIStatus,
  AISettings,
  AISettingsUpdate,
  BatchClaimExtractionResult,
  ChatResponse,
  ClaimExtractionResult,
  ClaimTransferRead,
  ComparisonGroup,
  ContactSummary,
  CreditorSummary,
  DashboardSummary,
  DocumentDetail,
  DocumentSummary,
  askChat,
  exportClaimsUrl,
  extractClaim,
  extractClaimsBatch,
  fetchAIStatus,
  fetchAISettings,
  fetchComparisons,
  fetchContacts,
  fetchCreditors,
  fetchDashboard,
  fetchDocument,
  fetchDocuments,
  fetchTransfers,
  importPaperless,
  saveAISettings,
} from "./services/api";

type View = "documents" | "creditors" | "contacts" | "transfers" | "dashboard" | "comparison" | "chat";

function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("de-DE").format(new Date(value));
}

function formatMoney(value: string | number | null | undefined, currency = "EUR"): string {
  const numberValue = Number(value ?? 0);
  return new Intl.NumberFormat("de-DE", { style: "currency", currency }).format(numberValue);
}

export default function App() {
  const [view, setView] = useState<View>("documents");
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [creditors, setCreditors] = useState<CreditorSummary[]>([]);
  const [contacts, setContacts] = useState<ContactSummary[]>([]);
  const [transfers, setTransfers] = useState<ClaimTransferRead[]>([]);
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [comparisons, setComparisons] = useState<ComparisonGroup[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);
  const [aiSettings, setAISettings] = useState<AISettings | null>(null);
  const [aiSecrets, setAISecrets] = useState({ openai: "", gemini: "", anthropic: "" });
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [batchExtracting, setBatchExtracting] = useState(false);
  const [extractionResult, setExtractionResult] = useState<ClaimExtractionResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchClaimExtractionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentDetail | null>(null);
  const [question, setQuestion] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);

  const hasDocuments = useMemo(() => documents.length > 0, [documents]);

  async function loadDocuments(query = search) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDocuments(query);
      setDocuments(data.items);
      setTotal(data.total);
    } catch (err) {
      setError("Dokumente konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function loadCreditors() {
    setLoading(true);
    setError(null);
    try {
      setCreditors(await fetchCreditors());
    } catch (err) {
      setError("Glaeubiger konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function loadDashboard() {
    setLoading(true);
    setError(null);
    try {
      setDashboard(await fetchDashboard());
    } catch (err) {
      setError("Dashboard konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function loadContacts() {
    setLoading(true);
    setError(null);
    try {
      setContacts(await fetchContacts());
    } catch (err) {
      setError("Kontakte konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function loadTransfers() {
    setLoading(true);
    setError(null);
    try {
      setTransfers(await fetchTransfers());
    } catch (err) {
      setError("Forderungswechsel konnten nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function loadComparisons() {
    setLoading(true);
    setError(null);
    try {
      setComparisons(await fetchComparisons());
    } catch (err) {
      setError("Vergleich konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }

  async function refreshCurrentView(nextView = view) {
    if (nextView === "documents") await loadDocuments();
    if (nextView === "creditors") await loadCreditors();
    if (nextView === "contacts") await loadContacts();
    if (nextView === "transfers") await loadTransfers();
    if (nextView === "dashboard") await loadDashboard();
    if (nextView === "comparison") await loadComparisons();
  }

  async function handleImport() {
    setImporting(true);
    setError(null);
    try {
      await importPaperless();
      await loadDocuments();
    } catch (err) {
      setError("Paperless-Import ist fehlgeschlagen. Pruefe URL und Zugangsdaten.");
    } finally {
      setImporting(false);
    }
  }

  async function loadAIStatus() {
    setSettingsLoading(true);
    try {
      const [status, settings] = await Promise.all([fetchAIStatus(), fetchAISettings()]);
      setAIStatus(status);
      setAISettings(settings);
      setAISecrets({ openai: "", gemini: "", anthropic: "" });
    } catch (err) {
      setError("KI-Einstellungen konnten nicht geladen werden.");
    } finally {
      setSettingsLoading(false);
    }
  }

  async function handleSaveAISettings() {
    if (!aiSettings) return;
    setSettingsSaving(true);
    setError(null);
    try {
      const payload: AISettingsUpdate = {
        mode: aiSettings.mode,
        provider: aiSettings.provider,
        openai_model: aiSettings.openai_model,
        openai_api_base_url: aiSettings.openai_api_base_url,
        openai_api_key: aiSecrets.openai || null,
        gemini_model: aiSettings.gemini_model,
        gemini_api_base_url: aiSettings.gemini_api_base_url,
        gemini_api_key: aiSecrets.gemini || null,
        anthropic_model: aiSettings.anthropic_model,
        anthropic_api_base_url: aiSettings.anthropic_api_base_url,
        anthropic_api_key: aiSecrets.anthropic || null,
        ollama_model: aiSettings.ollama_model,
        ollama_base_url: aiSettings.ollama_base_url,
      };
      const saved = await saveAISettings(payload);
      setAISettings(saved);
      setAISecrets({ openai: "", gemini: "", anthropic: "" });
      setAIStatus(await fetchAIStatus());
    } catch (err) {
      setError("KI-Einstellungen konnten nicht gespeichert werden.");
    } finally {
      setSettingsSaving(false);
    }
  }

  function patchAISettings(patch: Partial<AISettings>) {
    setAISettings((current) => (current ? { ...current, ...patch } : current));
  }

  function openSettings() {
    setSettingsOpen(true);
    void loadAIStatus();
  }

  async function openDocument(document: DocumentSummary) {
    setError(null);
    setExtractionResult(null);
    try {
      setSelected(await fetchDocument(document.id));
    } catch (err) {
      setError("Dokument konnte nicht geoeffnet werden.");
    }
  }

  async function handleExtractClaim() {
    if (!selected) return;
    setExtracting(true);
    setError(null);
    try {
      setExtractionResult(await extractClaim(selected.id));
      await loadCreditors();
      await loadContacts();
      await loadTransfers();
      await loadDashboard();
    } catch (err) {
      setError("Forderung konnte nicht erkannt werden. Pruefe KI-Anbieter und OCR-Text.");
    } finally {
      setExtracting(false);
    }
  }

  async function handleBatchExtractClaims() {
    if (documents.length === 0) return;
    setBatchExtracting(true);
    setBatchResult(null);
    setError(null);
    try {
      const result = await extractClaimsBatch(documents.map((document) => document.id));
      setBatchResult(result);
      await loadCreditors();
      await loadContacts();
      await loadTransfers();
      await loadDashboard();
    } catch (err) {
      setError("Stapelverarbeitung ist fehlgeschlagen. Pruefe KI-Anbieter und OCR-Texte.");
    } finally {
      setBatchExtracting(false);
    }
  }

  async function handleChat() {
    if (!question.trim()) return;
    setChatLoading(true);
    setError(null);
    try {
      setChatResponse(await askChat(question.trim()));
    } catch (err) {
      setError("Chat konnte nicht antworten. Pruefe KI-Anbieter und Dokumente.");
    } finally {
      setChatLoading(false);
    }
  }

  function changeView(nextView: View) {
    setView(nextView);
    void refreshCurrentView(nextView);
  }

  useEffect(() => {
    void loadDocuments("");
    void loadCreditors();
    void loadContacts();
    void loadTransfers();
    void loadDashboard();
    void loadComparisons();
  }, []);

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f6f7f9" }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="h1" sx={{ flexGrow: 1, fontWeight: 700 }}>
            DebtAI
          </Typography>
          <Tooltip title="Export">
            <IconButton component="a" href={exportClaimsUrl()}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Neu laden">
            <IconButton onClick={() => void refreshCurrentView()} disabled={loading || importing}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Einstellungen">
            <IconButton onClick={openSettings}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={importing ? <CircularProgress size={18} color="inherit" /> : <SyncIcon />}
            onClick={() => void handleImport()}
            disabled={importing}
          >
            Paperless importieren
          </Button>
        </Toolbar>
        <Tabs value={view} onChange={(_, value) => changeView(value)} sx={{ px: 3 }}>
          <Tab value="documents" label="Dokumente" />
          <Tab value="creditors" label="Glaeubiger" />
          <Tab value="contacts" label="Kontakte" />
          <Tab value="transfers" label="Wechsel" />
          <Tab value="dashboard" label="Dashboard" />
          <Tab value="comparison" label="Vergleich" />
          <Tab value="chat" label="Chat" />
        </Tabs>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}
          {view === "documents" && renderDocuments()}
          {view === "creditors" && renderCreditors()}
          {view === "contacts" && renderContacts()}
          {view === "transfers" && renderTransfers()}
          {view === "dashboard" && renderDashboard()}
          {view === "comparison" && renderComparison()}
          {view === "chat" && renderChat()}
        </Stack>
      </Container>

      {renderDocumentDialog()}
      {renderSettingsDialog()}
    </Box>
  );

  function renderDocuments() {
    return (
      <>
        <Paper variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
          <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems={{ md: "center" }}>
            <TextField
              fullWidth
              size="small"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void loadDocuments();
              }}
              placeholder="Suche"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <Button variant="outlined" onClick={() => void loadDocuments()} sx={{ minWidth: 120 }}>
              Suchen
            </Button>
            <Button
              variant="contained"
              onClick={() => void handleBatchExtractClaims()}
              disabled={batchExtracting || documents.length === 0}
              startIcon={batchExtracting ? <CircularProgress color="inherit" size={16} /> : undefined}
              sx={{ minWidth: 190 }}
            >
              Forderungen pruefen
            </Button>
            <Chip label={`${total} Dokumente`} />
          </Stack>
        </Paper>

        {batchResult && (
          <Alert severity={batchResult.failed > 0 ? "warning" : "success"}>
            Stapelverarbeitung fertig: {batchResult.claims_created_or_updated} Forderungen gespeichert,{" "}
            {batchResult.no_claim} ohne Forderung, {batchResult.skipped} uebersprungen, {batchResult.failed} fehlgeschlagen.
          </Alert>
        )}

        <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Datei</TableCell>
                <TableCell>Typ</TableCell>
                <TableCell>Datum</TableCell>
                <TableCell>Paperless-ID</TableCell>
                <TableCell>Importiert</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && loadingRow(5)}
              {!loading && !hasDocuments && emptyRow(5, "Keine Dokumente")}
              {!loading &&
                documents.map((document) => (
                  <TableRow
                    hover
                    key={document.id}
                    onClick={() => void openDocument(document)}
                    sx={{ cursor: "pointer" }}
                  >
                    <TableCell>{document.filename}</TableCell>
                    <TableCell>{document.document_type ?? "-"}</TableCell>
                    <TableCell>{formatDate(document.document_date)}</TableCell>
                    <TableCell>{document.paperless_id}</TableCell>
                    <TableCell>{formatDate(document.imported_at)}</TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
      </>
    );
  }

  function renderCreditors() {
    return (
      <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Glaeubiger</TableCell>
              <TableCell>Forderungen</TableCell>
              <TableCell>Offen</TableCell>
              <TableCell>Gesamt</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && loadingRow(5)}
            {!loading && creditors.length === 0 && emptyRow(5, "Keine Glaeubiger")}
            {!loading &&
              creditors.map((creditor) => (
                <TableRow hover key={creditor.id}>
                  <TableCell>{creditor.canonical_name}</TableCell>
                  <TableCell>{creditor.claim_count}</TableCell>
                  <TableCell>{formatMoney(creditor.open_amount)}</TableCell>
                  <TableCell>{formatMoney(creditor.total_amount)}</TableCell>
                  <TableCell>
                    <Chip size="small" label={creditor.active ? "aktiv" : "inaktiv"} />
                  </TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  function renderContacts() {
    return (
      <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Adresse</TableCell>
              <TableCell>E-Mail</TableCell>
              <TableCell>Telefon</TableCell>
              <TableCell>Dokumente</TableCell>
              <TableCell>Glaeubiger</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && loadingRow(6)}
            {!loading && contacts.length === 0 && emptyRow(6, "Keine Kontakte")}
            {!loading &&
              contacts.map((contact) => (
                <TableRow hover key={contact.id}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 700 }}>
                      {contact.display_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {contact.person_name ?? contact.organization_name ?? "-"}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {[contact.street, [contact.postal_code, contact.city].filter(Boolean).join(" "), contact.country]
                      .filter(Boolean)
                      .join(", ") || "-"}
                  </TableCell>
                  <TableCell>{contact.email ?? "-"}</TableCell>
                  <TableCell>{contact.phone ?? "-"}</TableCell>
                  <TableCell>{contact.document_count}</TableCell>
                  <TableCell>{contact.creditor_count}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  function renderTransfers() {
    return (
      <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Datum</TableCell>
              <TableCell>Forderung</TableCell>
              <TableCell>Von</TableCell>
              <TableCell>Zu</TableCell>
              <TableCell>Dokument</TableCell>
              <TableCell>Notiz</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && loadingRow(6)}
            {!loading && transfers.length === 0 && emptyRow(6, "Noch keine Forderungswechsel erkannt")}
            {!loading &&
              transfers.map((transfer) => (
                <TableRow hover key={transfer.id}>
                  <TableCell>{formatDate(transfer.transfer_date ?? transfer.created_at)}</TableCell>
                  <TableCell>{transfer.claim_reference ?? transfer.contract_reference ?? `#${transfer.claim_id}`}</TableCell>
                  <TableCell>{transfer.from_creditor_name ?? "-"}</TableCell>
                  <TableCell>{transfer.to_creditor_name ?? "-"}</TableCell>
                  <TableCell>{transfer.document_filename ?? "-"}</TableCell>
                  <TableCell>{transfer.notes ?? "-"}</TableCell>
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  function renderDashboard() {
    return (
      <Stack spacing={2}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
          {metric("Dokumente", dashboard?.document_count ?? 0)}
          {metric("Glaeubiger", dashboard?.creditor_count ?? 0)}
          {metric("Forderungen", dashboard?.claim_count ?? 0)}
          {metric("Offen", formatMoney(dashboard?.open_claim_amount))}
          {metric("Betitelt", dashboard?.titled_claim_count ?? 0)}
        </Stack>
        <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1 }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Anzahl</TableCell>
                <TableCell>Betrag</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && loadingRow(3)}
              {!loading && (dashboard?.status_buckets.length ?? 0) === 0 && emptyRow(3, "Keine Forderungen")}
              {!loading &&
                dashboard?.status_buckets.map((bucket) => (
                  <TableRow key={bucket.status}>
                    <TableCell>{bucket.status}</TableCell>
                    <TableCell>{bucket.count}</TableCell>
                    <TableCell>{formatMoney(bucket.amount)}</TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Stack>
    );
  }

  function renderChat() {
    return (
      <Stack spacing={2}>
        <Paper variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
          <Stack spacing={2}>
            <TextField
              fullWidth
              multiline
              minRows={3}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Frage zu deinen Dokumenten"
            />
            <Button
              variant="contained"
              onClick={() => void handleChat()}
              disabled={chatLoading || !question.trim()}
              sx={{ alignSelf: "flex-start" }}
            >
              {chatLoading ? "Frage laeuft" : "Fragen"}
            </Button>
          </Stack>
        </Paper>
        {chatResponse && (
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
            <Stack spacing={2}>
              <Typography variant="body1" sx={{ whiteSpace: "pre-wrap" }}>
                {chatResponse.answer}
              </Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <Chip size="small" label={`${chatResponse.provider} / ${chatResponse.model}`} />
                <Chip size="small" label={`${chatResponse.sources.length} Quellen`} />
              </Stack>
              {chatResponse.sources.map((source) => (
                <Box key={source.document_id}>
                  <Typography variant="subtitle2">{source.filename}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {source.snippet}
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Paper>
        )}
      </Stack>
    );
  }

  function renderComparison() {
    return (
      <Stack spacing={2}>
        {loading && (
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <CircularProgress size={20} />
              <Typography variant="body2">Laedt</Typography>
            </Stack>
          </Paper>
        )}
        {!loading && comparisons.length === 0 && (
          <Paper variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
            <Typography variant="body2">Keine moeglichen Doppelungen oder Vergleichstreffer</Typography>
          </Paper>
        )}
        {!loading &&
          comparisons.map((group, index) => (
            <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: 1 }} key={`${group.reason}-${index}`}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell colSpan={5}>{group.reason}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Glaeubiger</TableCell>
                    <TableCell>Betrag</TableCell>
                    <TableCell>Aktenzeichen</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {group.items.map((item) => (
                    <TableRow key={item.claim_id}>
                      <TableCell>{item.claim_id}</TableCell>
                      <TableCell>{item.creditor ?? "-"}</TableCell>
                      <TableCell>{formatMoney(item.amount, item.currency)}</TableCell>
                      <TableCell>{item.claim_reference ?? item.contract_reference ?? "-"}</TableCell>
                      <TableCell>{item.status}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ))}
      </Stack>
    );
  }

  function renderDocumentDialog() {
    return (
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} fullWidth maxWidth="md">
        <DialogTitle>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} alignItems={{ sm: "center" }}>
            <Typography variant="h6" component="span" sx={{ flexGrow: 1 }}>
              {selected?.filename}
            </Typography>
            <Button
              size="small"
              variant="contained"
              onClick={() => void handleExtractClaim()}
              disabled={!selected?.ocr_text || extracting}
              startIcon={extracting ? <CircularProgress color="inherit" size={16} /> : undefined}
            >
              Forderung erkennen
            </Button>
          </Stack>
        </DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Chip size="small" label={`Paperless ${selected?.paperless_id ?? ""}`} />
              <Chip size="small" label={selected?.document_type ?? "Ohne Typ"} />
              <Chip size="small" label={formatDate(selected?.document_date ?? null)} />
            </Stack>
            {extractionResult && (
              <Alert severity={extractionResult.has_claim ? "success" : "info"}>
                {extractionResult.has_claim
                  ? `Forderung gespeichert: ${extractionResult.extracted.creditor_name ?? "Unbekannter Glaeubiger"}${
                      extractionResult.extracted.amount
                        ? `, ${extractionResult.extracted.amount} ${extractionResult.extracted.currency}`
                        : ""
                    }${
                      extractionResult.extracted.claim_reference
                        ? `, Aktenzeichen ${extractionResult.extracted.claim_reference}`
                        : ""
                    }`
                  : "Keine Forderung in diesem Dokument erkannt."}
              </Alert>
            )}
            <Typography
              component="pre"
              variant="body2"
              sx={{
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                m: 0,
                maxHeight: "60vh",
                overflow: "auto",
                bgcolor: "#f6f7f9",
                p: 2,
                borderRadius: 1,
              }}
            >
              {selected?.ocr_text || "Kein OCR-Text vorhanden"}
            </Typography>
          </Stack>
        </DialogContent>
      </Dialog>
    );
  }

  function renderSettingsDialog() {
    const mode = aiSettings?.mode ?? "none";
    const onlineDisabled = mode !== "online";
    const offlineDisabled = mode !== "offline";
    return (
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Einstellungen</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={3}>
            <Box>
              <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={2}>
                <Typography variant="h6" component="h2">
                  KI-Anbieter
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={settingsLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
                  onClick={() => void loadAIStatus()}
                  disabled={settingsLoading}
                >
                  Aktualisieren
                </Button>
              </Stack>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 2 }}>
                <Chip
                  color={aiStatus?.configured_provider && aiStatus.configured_provider !== "none" ? "success" : "default"}
                  label={`Aktiv: ${aiStatus?.configured_provider ?? "wird geladen"}`}
                />
                <Chip label={`Modus: ${aiStatus?.mode ?? mode}`} />
                <Chip label={`${aiStatus?.available_providers.length ?? 0} Anbieter bereit`} />
                <Chip
                  icon={aiStatus?.ollama_available ? <CheckCircleIcon /> : <CancelIcon />}
                  color={aiStatus?.ollama_available ? "success" : "default"}
                  label={aiStatus?.ollama_available ? "Ollama erreichbar" : "Ollama nicht erreichbar"}
                />
              </Stack>
            </Box>

            {settingsLoading && (
              <Stack direction="row" gap={1} alignItems="center">
                <CircularProgress size={20} />
                <Typography variant="body2">Laedt Einstellungen</Typography>
              </Stack>
            )}

            {aiSettings && (
              <>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                    Betriebsart
                  </Typography>
                  <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                    <Button
                      variant={mode === "offline" ? "contained" : "outlined"}
                      onClick={() => patchAISettings({ mode: "offline", provider: "none" })}
                    >
                      Lokal mit Ollama
                    </Button>
                    <Button
                      variant={mode === "online" ? "contained" : "outlined"}
                      onClick={() => patchAISettings({ mode: "online", provider: aiSettings.provider === "none" ? "openai" : aiSettings.provider })}
                    >
                      Online-Anbieter
                    </Button>
                    <Button variant={mode === "none" ? "contained" : "outlined"} onClick={() => patchAISettings({ mode: "none", provider: "none" })}>
                      Aus
                    </Button>
                  </Stack>
                </Box>

                <Divider />

                <Box sx={{ opacity: offlineDisabled ? 0.45 : 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                    Lokale KI
                  </Typography>
                  <Stack spacing={2}>
                    <TextField
                      label="Ollama Modell"
                      value={aiSettings.ollama_model}
                      disabled={offlineDisabled}
                      onChange={(event) => patchAISettings({ ollama_model: event.target.value })}
                      helperText="Beispiel: qwen3:14b, llama3.1:8b oder mistral"
                    />
                    <TextField
                      label="Ollama Adresse"
                      value={aiSettings.ollama_base_url}
                      disabled={offlineDisabled}
                      onChange={(event) => patchAISettings({ ollama_base_url: event.target.value })}
                      helperText={`Windows-Standard: http://host.docker.internal:11434${
                        aiStatus?.ollama_detected_url ? `, erkannt: ${aiStatus.ollama_detected_url}` : ""
                      }`}
                    />
                  </Stack>
                </Box>

                <Divider />

                <Box sx={{ opacity: onlineDisabled ? 0.45 : 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                    Online-KI
                  </Typography>
                  <Stack spacing={2}>
                    <TextField
                      select
                      label="Anbieter"
                      value={aiSettings.provider}
                      disabled={onlineDisabled}
                      onChange={(event) => patchAISettings({ provider: event.target.value })}
                    >
                      <MenuItem value="openai">OpenAI</MenuItem>
                      <MenuItem value="gemini">Gemini</MenuItem>
                      <MenuItem value="anthropic">Claude / Anthropic</MenuItem>
                    </TextField>

                    {renderProviderFields("openai", "OpenAI", aiSettings.openai_api_key_set, aiSettings.openai_model, aiSettings.openai_api_base_url, onlineDisabled || aiSettings.provider !== "openai")}
                    {renderProviderFields("gemini", "Gemini", aiSettings.gemini_api_key_set, aiSettings.gemini_model, aiSettings.gemini_api_base_url, onlineDisabled || aiSettings.provider !== "gemini")}
                    {renderProviderFields("anthropic", "Claude / Anthropic", aiSettings.anthropic_api_key_set, aiSettings.anthropic_model, aiSettings.anthropic_api_base_url, onlineDisabled || aiSettings.provider !== "anthropic")}
                  </Stack>
                </Box>

                <Alert severity="info">
                  API-Schluessel werden gespeichert, aber nicht wieder angezeigt. Leere Schluessel-Felder behalten
                  vorhandene Werte bei.
                </Alert>

                <Stack direction="row" spacing={1} justifyContent="flex-end">
                  <Button variant="outlined" onClick={() => void loadAIStatus()} disabled={settingsLoading || settingsSaving}>
                    Verwerfen
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => void handleSaveAISettings()}
                    disabled={settingsSaving || settingsLoading}
                    startIcon={settingsSaving ? <CircularProgress color="inherit" size={16} /> : undefined}
                  >
                    Speichern
                  </Button>
                </Stack>
              </>
            )}
          </Stack>
        </DialogContent>
      </Dialog>
    );
  }

  function renderProviderFields(
    provider: "openai" | "gemini" | "anthropic",
    label: string,
    keySet: boolean,
    model: string,
    baseUrl: string,
    disabled: boolean,
  ) {
    const modelKey = `${provider}_model` as keyof AISettings;
    const baseUrlKey = `${provider}_api_base_url` as keyof AISettings;
    return (
      <Paper variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
              {label}
            </Typography>
            <Chip size="small" color={keySet ? "success" : "default"} label={keySet ? "Schluessel gesetzt" : "kein Schluessel"} />
          </Stack>
          <TextField
            label="Modell"
            value={model}
            disabled={disabled}
            onChange={(event) => patchAISettings({ [modelKey]: event.target.value } as Partial<AISettings>)}
          />
          <TextField
            label="API Adresse"
            value={baseUrl}
            disabled={disabled}
            onChange={(event) => patchAISettings({ [baseUrlKey]: event.target.value } as Partial<AISettings>)}
          />
          <TextField
            label="API-Schluessel"
            type="password"
            value={aiSecrets[provider]}
            disabled={disabled}
            placeholder={keySet ? "Vorhandenen Schluessel behalten" : "Schluessel eintragen"}
            onChange={(event) => setAISecrets((current) => ({ ...current, [provider]: event.target.value }))}
          />
        </Stack>
      </Paper>
    );
  }
}

function metric(label: string, value: string | number) {
  return (
    <Paper variant="outlined" sx={{ p: 2, borderRadius: 1, flex: 1, minWidth: 160 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h5" sx={{ fontWeight: 700 }}>
        {value}
      </Typography>
    </Paper>
  );
}

function loadingRow(colSpan: number) {
  return (
    <TableRow>
      <TableCell colSpan={colSpan}>
        <Stack direction="row" gap={1} alignItems="center" sx={{ py: 2 }}>
          <CircularProgress size={20} />
          <Typography variant="body2">Laedt</Typography>
        </Stack>
      </TableCell>
    </TableRow>
  );
}

function emptyRow(colSpan: number, label: string) {
  return (
    <TableRow>
      <TableCell colSpan={colSpan}>
        <Typography variant="body2" sx={{ py: 2 }}>
          {label}
        </Typography>
      </TableCell>
    </TableRow>
  );
}
