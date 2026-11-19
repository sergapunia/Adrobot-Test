export type CatalogItem = {
  id: number;
  name: string;
};

export type StreamOffer = {
  keitaro_offer_id: number;
  name: string;
  share: number;
  is_pinned: boolean;
  status: "active" | "removed" | string;
};

export type Stream = {
  id: number;
  keitaro_id: number;
  name: string;
  is_dirty: boolean;
  has_offers: boolean;
  offers: StreamOffer[];
};

export type Campaign = {
  keitaro_id: number;
  name: string;
  alias: string;
  domain_id: number | null;
  group_id: number | null;
  traffic_source_id: number | null;
  campaign_url: string | null;
  streams: Stream[];
};

export type CreateCampaignPayload = {
  name: string;
  country_code: string;
  offer_id: number;
  domain_id: number;
  group_id?: number | null;
  traffic_source_id: number;
};
