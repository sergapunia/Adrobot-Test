import type { Campaign, CatalogItem, CreateCampaignPayload } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let detail = `Ошибка запроса (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
        detail = body.detail[0].msg;
      }
    } catch {
      // keep the status fallback
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  catalogs: {
    domains: () => request<CatalogItem[]>("/api/catalogs/domains"),
    groups: () => request<CatalogItem[]>("/api/catalogs/groups"),
    trafficSources: () => request<CatalogItem[]>("/api/catalogs/traffic-sources"),
    offers: (q?: string) =>
      request<CatalogItem[]>(`/api/catalogs/offers${q ? `?q=${encodeURIComponent(q)}` : ""}`),
    createDomain: (name: string) =>
      request<CatalogItem>("/api/catalogs/domains", { method: "POST", body: JSON.stringify({ name }) }),
    createGroup: (name: string) =>
      request<CatalogItem>("/api/catalogs/groups", { method: "POST", body: JSON.stringify({ name }) }),
    createTrafficSource: (name: string) =>
      request<CatalogItem>("/api/catalogs/traffic-sources", {
        method: "POST",
        body: JSON.stringify({ name }),
      }),
  },
  campaigns: {
    list: () => request<Campaign[]>("/api/campaigns"),
    get: (id: number) => request<Campaign>(`/api/campaigns/${id}`),
    create: (payload: CreateCampaignPayload) =>
      request<Campaign>("/api/campaigns", { method: "POST", body: JSON.stringify(payload) }),
    fetchStreams: (id: number) =>
      request<Campaign>(`/api/campaigns/${id}/fetch-streams`, { method: "POST" }),
  },
  streams: {
    addOffer: (streamId: number, offerId: number) =>
      request<Campaign>(`/api/streams/${streamId}/offers`, {
        method: "POST",
        body: JSON.stringify({ offer_id: offerId }),
      }),
    removeOffer: (streamId: number, offerId: number) =>
      request<Campaign>(`/api/streams/${streamId}/offers/${offerId}/remove`, { method: "POST" }),
    restoreOffer: (streamId: number, offerId: number) =>
      request<Campaign>(`/api/streams/${streamId}/offers/${offerId}/restore`, { method: "POST" }),
    pinOffer: (streamId: number, offerId: number, pinned: boolean, share?: number) =>
      request<Campaign>(`/api/streams/${streamId}/offers/${offerId}/pin`, {
        method: "POST",
        body: JSON.stringify({ pinned, share }),
      }),
    push: (streamId: number) => request<Campaign>(`/api/streams/${streamId}/push`, { method: "POST" }),
    cancel: (streamId: number) =>
      request<Campaign>(`/api/streams/${streamId}/cancel`, { method: "POST" }),
  },
};
