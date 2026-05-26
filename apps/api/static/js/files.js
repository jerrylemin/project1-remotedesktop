async function uploadArtifact(fileInput) {
  if (!fileInput.files.length) throw new Error("Choose a file first");
  const form = new FormData();
  form.append("file", fileInput.files[0]);
  const res = await fetch("/api/files/upload", { method: "POST", body: form });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

async function dispatchArtifact(artifactId, machineId) {
  const res = await fetch(`/api/files/${encodeURIComponent(artifactId)}/dispatch?machine_id=${encodeURIComponent(machineId)}`, { method: "POST" });
  if (!res.ok) throw new Error("Dispatch failed");
  return res.json();
}

window.TelepcFiles = { uploadArtifact, dispatchArtifact };
