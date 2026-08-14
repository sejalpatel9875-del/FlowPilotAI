"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Drawer } from "@/components/ui/Drawer";
import { Toast, ToastType } from "@/components/ui/Toast";
import { Tabs } from "@/components/ui/Tabs";
import {
  BookOpen,
  Upload,
  Search,
  MessageSquare,
  FileText,
  Trash2,
  Eye,
  CheckCircle2,
  Sparkles,
  Send,
  HelpCircle,
  AlertCircle,
  File,
  Layers,
  ArrowRight,
  ShieldCheck
} from "lucide-react";

interface DocItem {
  id: string;
  title: string;
  fileType: string;
  chunkCount: number;
  status: string;
  createdAt: string;
}

interface Citation {
  documentTitle: string;
  documentId: string;
  chunkIndex: number;
  fileType: string;
  relevanceScore: number;
  snippet: string;
}

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  citations?: Citation[];
  confidenceScore?: number;
  hasRelevantDocs?: boolean;
}

export default function KnowledgeVaultPage() {
  const [activeTab, setActiveTab] = useState("vault");
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [previewDoc, setPreviewDoc] = useState<any>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  // RAG Chat State
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "msg-welcome",
      sender: "assistant",
      text: "Welcome to your RAG Knowledge Vault! Ask any question about your uploaded documents, and I will retrieve answers with precise citations.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);

  const [toast, setToast] = useState<{ type: ToastType; title: string; message?: string } | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/knowledge/documents", {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error("Failed to load documents", err);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setToast(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("http://localhost:8000/api/v1/knowledge/upload", {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed.");
      }

      const newDoc = await res.json();
      setToast({ type: "success", title: "Document Indexed", message: `Successfully chunked and indexed '${newDoc.title}'.` });
      setSelectedFile(null);
      setIsUploadModalOpen(false);
      fetchDocuments();
    } catch (err: any) {
      setToast({ type: "error", title: "Upload Failed", message: err.message });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDoc = async (id: string, title: string) => {
    if (!confirm(`Are you sure you want to delete '${title}' from your vault?`)) return;

    try {
      const res = await fetch(`http://localhost:8000/api/v1/knowledge/documents/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.ok) {
        setToast({ type: "success", title: "Document Removed", message: `Deleted '${title}'.` });
        fetchDocuments();
      }
    } catch (err) {
      setToast({ type: "error", title: "Delete Error", message: "Failed to delete document." });
    }
  };

  const handlePreviewDoc = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/knowledge/documents/${id}`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setPreviewDoc(data);
        setIsPreviewOpen(true);
      }
    } catch (err) {
      setToast({ type: "error", title: "Preview Error", message: "Could not load document preview." });
    }
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || isChatLoading) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: "user",
      text: chatInput,
    };

    setChatMessages((prev) => [...prev, userMsg]);
    const queryText = chatInput;
    setChatInput("");
    setIsChatLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/knowledge/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ query: queryText }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "RAG query error.");
      }

      const data = await res.json();
      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: "assistant",
        text: data.answer,
        citations: data.citations,
        confidenceScore: data.confidenceScore,
        hasRelevantDocs: data.hasRelevantDocs,
      };

      setChatMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          id: `bot_${Date.now()}`,
          sender: "assistant",
          text: `[RAG Error]: ${err.message}`,
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const filteredDocs = documents.filter((doc) =>
    doc.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-blue-400" />
            RAG Knowledge Vault
          </h1>
          <p className="text-xs text-muted-foreground">
            Multi-tenant AI vector vault. Upload PDF, TXT, and Markdown files to query your knowledge securely.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="md"
            onClick={() => setIsUploadModalOpen(true)}
            leftIcon={<Upload className="h-4 w-4" />}
          >
            Upload Document
          </Button>
        </div>
      </div>

      {toast && (
        <Toast type={toast.type} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
      )}

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: "vault", label: `Knowledge Base (${documents.length})`, icon: <FileText className="h-4 w-4" /> },
          { id: "ask", label: "Ask Your Knowledge (RAG)", icon: <Sparkles className="h-4 w-4 text-purple-400" /> },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* TAB 1: KNOWLEDGE BASE VAULT */}
      {activeTab === "vault" && (
        <div className="space-y-6">
          {/* Search Bar */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search uploaded documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl glass-panel bg-secondary/30 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/60"
              />
            </div>
          </div>

          {/* Document List */}
          {filteredDocs.length === 0 ? (
            <Card glass className="p-8 text-center space-y-3">
              <BookOpen className="h-10 w-10 text-muted-foreground mx-auto" />
              <h3 className="text-base font-semibold text-foreground">No Documents in Vault</h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Upload your freelancing contracts, client briefs, and notes to enable AI semantic RAG search.
              </p>
              <Button variant="outline" size="sm" onClick={() => setIsUploadModalOpen(true)}>
                Upload First File
              </Button>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDocs.map((doc) => (
                <Card key={doc.id} glass className="p-4 flex flex-col justify-between space-y-4 hover:border-primary/40 transition-all">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-xs">
                          {doc.fileType.toUpperCase()}
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-foreground truncate max-w-[180px]">{doc.title}</h4>
                          <span className="text-[10px] text-muted-foreground font-mono">{doc.createdAt}</span>
                        </div>
                      </div>
                      <Badge variant="completed" className="font-mono text-[10px]">
                        <CheckCircle2 className="h-3 w-3 mr-1 text-emerald-400" />
                        {doc.status}
                      </Badge>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-border/50 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground font-mono">{doc.chunkCount} Chunks Indexed</span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handlePreviewDoc(doc.id)}
                        className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                        title="Preview text chunks"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteDoc(doc.id, doc.title)}
                        className="p-1.5 rounded-lg hover:bg-rose-500/10 text-muted-foreground hover:text-rose-400 transition-colors"
                        title="Delete document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: ASK YOUR KNOWLEDGE (RAG CHAT) */}
      {activeTab === "ask" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Panel (2 Cols) */}
          <Card glass className="lg:col-span-2 flex flex-col h-[600px]">
            <CardHeader className="border-b border-border/60 pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-400" />
                Ask Your Knowledge Vault
              </CardTitle>
              <CardDescription>Retrieves relevant chunks with non-hallucinated citations</CardDescription>
            </CardHeader>

            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-xs space-y-3 ${
                      msg.sender === "user"
                        ? "bg-primary text-white"
                        : "glass-panel bg-secondary/50 text-foreground border border-border/60"
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>

                    {/* Citations & Relevance Badge */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-3 border-t border-border/50 space-y-2 text-[11px]">
                        <div className="flex items-center justify-between font-semibold text-purple-300">
                          <span>Source Citations ({msg.citations.length})</span>
                          {msg.confidenceScore && (
                            <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              {msg.confidenceScore}% Relevance
                            </span>
                          )}
                        </div>
                        <div className="space-y-1.5">
                          {msg.citations.map((cite, idx) => (
                            <div key={idx} className="p-2 rounded-lg bg-card/60 border border-border/40 font-mono text-[10px]">
                              <div className="flex items-center justify-between text-indigo-300 font-bold">
                                <span>📄 {cite.documentTitle}</span>
                                <span>Chunk #{cite.chunkIndex}</span>
                              </div>
                              <p className="text-muted-foreground mt-1 line-clamp-2 italic">"{cite.snippet}"</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isChatLoading && (
                <div className="flex items-center gap-2 text-xs text-purple-400">
                  <Sparkles className="h-4 w-4 animate-spin" />
                  <span>Searching vector index & generating response...</span>
                </div>
              )}
            </CardContent>

            {/* Chat Input */}
            <div className="p-3 border-t border-border/60 flex items-center gap-2">
              <input
                type="text"
                placeholder="Ask a question about your uploaded documents..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                className="flex-1 rounded-xl glass-panel bg-secondary/40 px-4 py-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary border-border/60"
              />
              <Button variant="primary" size="md" onClick={handleSendChat} isLoading={isChatLoading}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </Card>

          {/* Right Panel: Vault Guidance */}
          <Card glass className="space-y-4">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                RAG Security & Rules
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-muted-foreground">
              <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                <h5 className="font-semibold text-foreground">Strict Tenant Isolation</h5>
                <p className="text-[11px]">Your uploaded documents are scoped exclusively to your user ID. Cross-tenant retrieval is strictly prohibited.</p>
              </div>

              <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                <h5 className="font-semibold text-foreground">No Citation Hallucination</h5>
                <p className="text-[11px]">If no relevant document chunks are found, the system clearly notifies you rather than inventing fake citations.</p>
              </div>

              <div className="p-3 rounded-xl bg-card/60 border border-border/50 space-y-1">
                <h5 className="font-semibold text-foreground">Supported Formats</h5>
                <p className="text-[11px]">PDF documents, plain text (.txt), and Markdown (.md) up to 25 MB.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* UPLOAD MODAL */}
      <Modal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        title="Upload Document to Vault"
      >
        <form onSubmit={handleUploadSubmit} className="space-y-4 text-xs">
          <div className="border-2 border-dashed border-border/80 rounded-2xl p-6 text-center space-y-2 hover:border-primary transition-colors cursor-pointer bg-secondary/20">
            <Upload className="h-8 w-8 text-primary mx-auto" />
            <div className="space-y-1">
              <p className="font-semibold text-foreground">Click to browse or drop file</p>
              <p className="text-[11px] text-muted-foreground">PDF, TXT, or Markdown (Max 25 MB)</p>
            </div>
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-muted-foreground mt-2"
            />
          </div>

          {selectedFile && (
            <div className="p-3 rounded-xl bg-card border border-border/60 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <File className="h-4 w-4 text-indigo-400" />
                <span className="font-semibold text-foreground">{selectedFile.name}</span>
              </div>
              <span className="font-mono text-muted-foreground">{(selectedFile.size / 1024).toFixed(1)} KB</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="outline" size="sm" type="button" onClick={() => setIsUploadModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit" isLoading={isUploading} disabled={!selectedFile}>
              Upload & Index
            </Button>
          </div>
        </form>
      </Modal>

      {/* PREVIEW DRAWER */}
      <Drawer
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        title={previewDoc ? previewDoc.title : "Document Preview"}
      >
        {previewDoc && (
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between p-3 rounded-xl bg-card border border-border/50">
              <div>
                <span className="text-muted-foreground block text-[10px]">Type</span>
                <span className="font-semibold text-foreground uppercase">{previewDoc.fileType}</span>
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Total Chunks</span>
                <span className="font-semibold text-foreground">{previewDoc.chunks.length}</span>
              </div>
              <div>
                <span className="text-muted-foreground block text-[10px]">Indexed Date</span>
                <span className="font-semibold text-foreground font-mono">{previewDoc.createdAt}</span>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold text-foreground">Extracted Text Chunks</h4>
              {previewDoc.chunks.map((c: any) => (
                <div key={c.chunkIndex} className="p-3 rounded-xl glass-panel bg-secondary/30 border border-border/60 space-y-1 font-mono">
                  <span className="text-indigo-400 font-bold text-[10px]">Chunk #{c.chunkIndex}</span>
                  <p className="text-slate-200 text-xs whitespace-pre-wrap">{c.contentText}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
