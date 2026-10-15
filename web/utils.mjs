export function escapeHtml(input) {
  return String(input ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

export function readableError(status, detail = "") {
  if (status === 404 && /workspace|expired/i.test(detail)) {
    return "Your temporary document workspace expired or the backend restarted. Please index the documents again.";
  }
  if (status === 422) return "The service rejected the request. Check the document format, size, or question.";
  if (status === 429) return "The service is busy or rate-limited. Please try again later.";
  if (status === 502) return "The language model could not complete your request. Please try again shortly.";
  if (status === 503) return "The document engine is temporarily unavailable. Please retry shortly.";
  return `The document engine returned HTTP ${status}. ${detail ? "Check the service status and try again." : "Please retry."}`;
}

export function validateQuestion(question, topK) {
  if (typeof question !== "string" || !question.trim()) throw Error("Enter a research question first.");
  if (question.length > 2000) throw Error("Questions cannot exceed 2,000 characters.");
  if (!Number.isInteger(topK) || topK < 1 || topK > 10) throw Error("Evidence depth must be between 1 and 10.");
  return { question: question.trim(), top_k: topK };
}

export function formatElapsed(seconds) {
  const n = Math.max(0, Math.floor(seconds));
  return `${String(Math.floor(n / 60)).padStart(2, "0")}:${String(n % 60).padStart(2, "0")}`;
}

export function safeApiUrl(value) {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:" && !(url.protocol === "http:" && ["localhost", "127.0.0.1"].includes(url.hostname))) return null;
    if (url.username || url.password || url.search || url.hash) return null;
    return url.origin;
  } catch {
    return null;
  }
}
