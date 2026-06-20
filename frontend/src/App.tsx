import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
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
  IconButton,
  InputAdornment,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import {
  DocumentDetail,
  DocumentSummary,
  fetchDocument,
  fetchDocuments,
  importPaperless,
} from "./services/api";

function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Intl.DateTimeFormat("de-DE").format(new Date(value));
}

export default function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DocumentDetail | null>(null);

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

  async function openDocument(document: DocumentSummary) {
    setError(null);
    try {
      setSelected(await fetchDocument(document.id));
    } catch (err) {
      setError("Dokument konnte nicht geoeffnet werden.");
    }
  }

  useEffect(() => {
    void loadDocuments("");
  }, []);

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f6f7f9" }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="h1" sx={{ flexGrow: 1, fontWeight: 700 }}>
            DebtAI
          </Typography>
          <Tooltip title="Neu laden">
            <IconButton onClick={() => void loadDocuments()} disabled={loading || importing}>
              <RefreshIcon />
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
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}

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
              <Chip label={`${total} Dokumente`} />
            </Stack>
          </Paper>

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
                {loading && (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Stack direction="row" gap={1} alignItems="center" sx={{ py: 2 }}>
                        <CircularProgress size={20} />
                        <Typography variant="body2">Laedt</Typography>
                      </Stack>
                    </TableCell>
                  </TableRow>
                )}

                {!loading && !hasDocuments && (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Typography variant="body2" sx={{ py: 2 }}>
                        Keine Dokumente
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}

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
        </Stack>
      </Container>

      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} fullWidth maxWidth="md">
        <DialogTitle>{selected?.filename}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Chip size="small" label={`Paperless ${selected?.paperless_id ?? ""}`} />
              <Chip size="small" label={selected?.document_type ?? "Ohne Typ"} />
              <Chip size="small" label={formatDate(selected?.document_date ?? null)} />
            </Stack>
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
    </Box>
  );
}
