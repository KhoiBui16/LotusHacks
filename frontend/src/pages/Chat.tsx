import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useLanguage } from "@/contexts/LanguageContext";
import { useToast } from "@/hooks/use-toast";
import Navbar from "@/components/landing/Navbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Plus, MessageSquare, Trash2, Send, ChevronLeft, Loader,
} from "lucide-react";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/apiClient";
import type { ChatSessionListItem, ChatSession } from "@/lib/api";

export default function Chat() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { t } = useLanguage();
  const { toast } = useToast();
  const qc = useQueryClient();
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [messageInput, setMessageInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const bootstrapSessionId = searchParams.get("sessionId");

  const syncSessionParam = (sessionId: string | null) => {
    const next = new URLSearchParams(searchParams);
    if (sessionId) next.set("sessionId", sessionId);
    else next.delete("sessionId");
    setSearchParams(next, { replace: true });
  };

  const sessionsQuery = useQuery<ChatSessionListItem[], ApiError>({
    queryKey: ["chat-sessions"],
    queryFn: api.chat.listSessions,
  });

  const sessionQuery = useQuery<ChatSession, ApiError>({
    queryKey: ["chat-session", selectedSessionId],
    queryFn: () => api.chat.getSession(selectedSessionId as string),
    enabled: Boolean(selectedSessionId),
  });

  const createSessionMutation = useMutation({
    mutationFn: api.chat.createSession,
    onSuccess: (newSession) => {
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
      setSelectedSessionId(newSession.id);
      syncSessionParam(newSession.id);
      setMessageInput("");
    },
    onError: (err) => {
      toast({
        title: "Failed to create session",
        description: err instanceof Error ? err.message : "Please try again",
        variant: "destructive",
      });
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ sessionId, content }: { sessionId: string; content: string }) =>
      api.chat.sendMessage(sessionId, { content }),
    onSuccess: () => {
      setMessageInput("");
      qc.invalidateQueries({ queryKey: ["chat-session", selectedSessionId] });
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    },
    onError: (err) => {
      toast({
        title: "Failed to send message",
        description: err instanceof Error ? err.message : "Please try again",
        variant: "destructive",
      });
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (id: string) => api.chat.deleteSession(id),
    onSuccess: () => {
      setSelectedSessionId(null);
      syncSessionParam(null);
      qc.invalidateQueries({ queryKey: ["chat-sessions"] });
      toast({ title: "Session deleted" });
    },
    onError: (err) => {
      toast({
        title: "Failed to delete session",
        description: err instanceof Error ? err.message : "Please try again",
        variant: "destructive",
      });
    },
  });

  useEffect(() => {
    if (bootstrapSessionId && bootstrapSessionId !== selectedSessionId) {
      setSelectedSessionId(bootstrapSessionId);
    }
  }, [bootstrapSessionId, selectedSessionId]);

  // Auto-select first session when there is no bootstrapped session
  useEffect(() => {
    if (!bootstrapSessionId && !selectedSessionId && (sessionsQuery.data ?? []).length > 0) {
      setSelectedSessionId(sessionsQuery.data![0].id);
    }
  }, [bootstrapSessionId, sessionsQuery.data, selectedSessionId]);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessionQuery.data?.messages]);

  const handleSendMessage = () => {
    if (!messageInput.trim() || !selectedSessionId) return;
    sendMessageMutation.mutate({
      sessionId: selectedSessionId,
      content: messageInput.trim(),
    });
  };

  const sessions = sessionsQuery.data ?? [];
  const currentSession = sessionQuery.data;
  const messages = currentSession?.messages ?? [];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <div className="flex-1 flex overflow-hidden pt-16">
        {/* Sidebar */}
        <div className="w-64 border-r border-border bg-card flex flex-col">
          <div className="p-4 border-b border-border">
            <Button variant="outline" className="w-full mb-2" onClick={() => navigate("/incident-intake")}> 
              <ChevronLeft className="w-4 h-4 mr-1" /> Back to incident
            </Button>
            <Button
              className="w-full gap-2"
              onClick={() => createSessionMutation.mutate()}
              disabled={createSessionMutation.isPending}
            >
              <Plus className="w-4 h-4" />
              New chat
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto px-2 py-4 space-y-2">
            {sessions.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                No conversations yet
              </p>
            ) : (
              sessions.map((session) => (
                <div key={session.id} className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setSelectedSessionId(session.id);
                      syncSessionParam(session.id);
                    }}
                    className={`flex-1 text-left px-3 py-2 rounded-lg transition-colors text-sm truncate ${
                      selectedSessionId === session.id
                        ? "bg-primary/20 text-primary"
                        : "hover:bg-secondary text-foreground"
                    }`}
                  >
                    <MessageSquare className="w-3 h-3 mr-2 inline" />
                    {session.title}
                  </button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (confirm("Delete this conversation?")) {
                        deleteSessionMutation.mutate(session.id);
                      }
                    }}
                    disabled={deleteSessionMutation.isPending}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {!selectedSessionId || !currentSession ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <MessageSquare className="w-16 h-16 mx-auto text-muted-foreground" />
                <h2 className="text-xl font-display font-bold text-foreground">
                  Start a new conversation
                </h2>
                <p className="text-muted-foreground max-w-xs">
                  Click "New chat" to begin chatting with AI
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Messages Area */}
              <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-muted-foreground">Send a message to start</p>
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-4 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary text-foreground border border-border"
                        }`}
                      >
                        <p className="text-sm break-words whitespace-pre-wrap">{msg.content}</p>
                        <p
                          className={`text-xs mt-2 ${
                            msg.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground"
                          }`}
                        >
                          {new Date(msg.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                {sendMessageMutation.isPending && (
                  <div className="flex gap-4">
                    <div className="bg-secondary text-foreground border border-border px-4 py-3 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Loader className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-border bg-card px-6 py-4">
                <div className="flex gap-3">
                  <Input
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    placeholder="Type your message here... (Shift+Enter for new line)"
                    disabled={sendMessageMutation.isPending || !selectedSessionId}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={
                      !messageInput.trim() || sendMessageMutation.isPending || !selectedSessionId
                    }
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
