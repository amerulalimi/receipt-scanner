import "server-only";

import { apiFetch, apiPublicUploadFetch } from "@/lib/api/client";
import { requireSessionCookieHeader } from "@/lib/api/session";
import type {
  UploadSessionCloseData,
  UploadSessionCreateData,
  UploadSessionKeepAliveData,
  UploadSessionUploadData,
  UploadSessionValidateData,
} from "@/lib/api/types";

export async function createUploadSessionWithFastApi(taxYear?: number) {
  const cookie = await requireSessionCookieHeader();
  return apiFetch<UploadSessionCreateData>("/api/v1/upload-sessions", {
    method: "POST",
    body: taxYear ? { tax_year: taxYear } : {},
    cookie,
  });
}

export async function validateUploadSessionWithFastApi(token: string) {
  return apiFetch<UploadSessionValidateData>(
    `/api/v1/upload-sessions/${encodeURIComponent(token)}/validate`,
  );
}

export async function uploadViaSessionWithFastApi(token: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiPublicUploadFetch<UploadSessionUploadData>(
    `/api/v1/upload-sessions/${encodeURIComponent(token)}/upload`,
    formData,
  );
}

export async function keepAliveUploadSessionWithFastApi(token: string) {
  return apiFetch<UploadSessionKeepAliveData>(
    `/api/v1/upload-sessions/${encodeURIComponent(token)}/keep-alive`,
    { method: "POST" },
  );
}

export async function closeUploadSessionWithFastApi(token: string) {
  return apiFetch<UploadSessionCloseData>(
    `/api/v1/upload-sessions/${encodeURIComponent(token)}/close`,
    { method: "POST" },
  );
}
