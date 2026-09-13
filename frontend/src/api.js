export async function api(path, { method = "GET", token, json, form } = {}) {
  const headers = {};
  let body;

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (form) {
    body = form;
  } else if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  }

  const response = await fetch(path, { method, headers, body });
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    const error = new Error(formatDetail(data) || `Request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }

  return data;
}

function formatDetail(data) {
  if (!data) return "";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg || JSON.stringify(item)).join(", ");
  }
  return "";
}

export function loginRequest(email, password) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  return api("/auth/login", { method: "POST", form });
}

export function signupRequest(email, password) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  return api("/auth/signup", { method: "POST", form });
}

export function listTasks(token) {
  return api("/agent/timelines", { token });
}

export function getTask(token, id) {
  return api(`/agent/timelines/${id}`, { token });
}

export function ingestTask(token, { raw_data, topic }) {
  return api("/agent/ingest", {
    method: "POST",
    token,
    json: { raw_data: raw_data || null, topic: topic || null },
  });
}
