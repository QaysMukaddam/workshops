// Vite exposes env variables prefixed with VITE_ through import.meta.env.
// This is the base URL of your FastAPI backend, so it can be changed per
// environment (local dev vs deployed) without touching this code.
const API_BASE_URL = import.meta.env.VITE_API_URL;

// Holds a function to call whenever ANY request comes back 401
// (expired/invalid token). Starts as a no-op (does nothing) until
// AuthContext registers the real one when the app loads.
let unauthorizedHandler = () => {};

// Called once by AuthContext when the app loads, to register what
// should happen on a 401 (log out + redirect to /login). Exported so
// AuthContext.jsx can import and call it.
export function setUnauthorizedHandler(handler) {
  // Replace the no-op with the real handler function passed in.
  unauthorizedHandler = handler;
}

// A single shared function that every other function below calls.
// Attaches the JWT (if one is passed) as an Authorization header, and
// throws a real Error if the response wasn't successful, so callers can
// use normal try/catch instead of checking response.ok every time.
async function request(endpoint, options = {}, token = null) {
  // Start with the default JSON content-type header. ...options.headers
  // lets a caller add/override headers if they ever need to.
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // If we were given a token, attach it as a Bearer token — this is
  // exactly what your protected FastAPI routes expect.
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Make the actual network request, combining the base URL with the
  // specific endpoint path (e.g. "/notices").
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // A 401 means the token is missing, invalid, or expired — trigger the
  // registered handler (log out + redirect) before anything else runs.
  if (response.status === 401) {
    unauthorizedHandler();
  }

  // FastAPI's error responses come back as JSON with a "detail" field.
  // If the request failed, parse that out and throw it as a real error.
  if (!response.ok) {
    // .catch(() => ({})) guards against a response body that isn't
    // valid JSON at all, so this line itself can't throw.
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Request failed with status ${response.status}`);
  }

  // Some endpoints (like DELETE) may return no body — guard against
  // trying to parse empty responses as JSON.
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

// --- Auth ---

// Registers a new user. role defaults to MEMBER unless specified.
export function registerUser(username, password, role = 'MEMBER') {
  return request('/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, role }),
  });
}

// Logs in and returns { access_token, token_type }.
export function loginUser(username, password) {
  return request('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

// --- Notices ---

// Fetches every notice. Requires a token, since viewing is login-only.
export function getNotices(token) {
  return request('/notices', {}, token);
}

// Fetches a single notice (and bumps its view count on the backend).
export function getNotice(noticeId, token) {
  return request(`/notices/${noticeId}`, {}, token);
}

// Creates a notice. Only works if the token belongs to an ADMIN.
export function createNotice(name, message, token) {
  return request('/notices', {
    method: 'POST',
    body: JSON.stringify({ name, message }),
  }, token);
}

// Deletes a notice. Only works if the token belongs to an ADMIN.
export function deleteNotice(noticeId, token) {
  return request(`/notices/${noticeId}`, { method: 'DELETE' }, token);
}

// --- Comments ---

// Fetches every comment on a notice.
export function getComments(noticeId, token) {
  return request(`/notices/${noticeId}/comments`, {}, token);
}

// Posts a new comment under a notice.
export function postComment(noticeId, text, token) {
  return request(`/notices/${noticeId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  }, token);
}

// Deletes a comment. Backend only allows this if you wrote it, or you're
// an ADMIN.
export function deleteComment(commentId, token) {
  return request(`/comments/${commentId}`, { method: 'DELETE' }, token);
}

// --- Likes ---

// Likes a notice.
export function likeNotice(noticeId, token) {
  return request(`/notices/${noticeId}/like`, { method: 'POST' }, token);
}

// Removes your own like from a notice.
export function unlikeNotice(noticeId, token) {
  return request(`/notices/${noticeId}/like`, { method: 'DELETE' }, token);
}

// Likes a comment.
export function likeComment(commentId, token) {
  return request(`/comments/${commentId}/like`, { method: 'POST' }, token);
}

// Removes your own like from a comment.
export function unlikeComment(commentId, token) {
  return request(`/comments/${commentId}/like`, { method: 'DELETE' }, token);
}