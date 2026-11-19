import { FormEvent, useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { StreamCard } from "../components/StreamCard";
import type { Campaign } from "../types";

export function CampaignEditor() {
  const params = useParams();
  const navigate = useNavigate();
  const routeId = params.id ?? "";
  const [campaignId, setCampaignId] = useState(routeId);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (id: number) => {
    setBusy(true);
    setError("");
    try {
      setCampaign(await api.campaigns.fetchStreams(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить кампанию");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (routeId) {
      setCampaignId(routeId);
      void load(Number(routeId));
    }
  }, [routeId, load]);

  async function onFetch(event: FormEvent) {
    event.preventDefault();
    if (!campaignId) {
      return;
    }
    const id = Number(campaignId);
    await load(id);
    if (String(id) !== routeId) {
      navigate(`/campaigns/${id}`);
    }
  }

  async function mutate(action: () => Promise<Campaign>) {
    setBusy(true);
    setError("");
    try {
      setCampaign(await action());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка запроса");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <form className="card form" onSubmit={onFetch}>
        <h1>{campaign?.name ?? "Редактор"}</h1>
        {campaign?.campaign_url ? (
          <a className="campaign-url" href={campaign.campaign_url} target="_blank" rel="noreferrer">
            {campaign.campaign_url}
          </a>
        ) : null}
        <div className="toolbar">
          <label>
            ID кампании
            <input value={campaignId} onChange={(event) => setCampaignId(event.target.value)} />
          </label>
          <button className="btn primary" type="submit" disabled={busy || !campaignId}>
            {busy ? "Загрузка…" : "Загрузить потоки"}
          </button>
        </div>
      </form>

      {error ? <p className="error banner">{error}</p> : null}

      {campaign ? (
        <div className="stream-grid">
          {campaign.streams.map((stream) => (
            <StreamCard
              key={stream.id}
              stream={stream}
              busy={busy}
              onAdd={(offerId) => mutate(() => api.streams.addOffer(stream.id, offerId))}
              onRemove={(offerId) => mutate(() => api.streams.removeOffer(stream.id, offerId))}
              onRestore={(offerId) => mutate(() => api.streams.restoreOffer(stream.id, offerId))}
              onPin={(offerId, pinned) => mutate(() => api.streams.pinOffer(stream.id, offerId, pinned))}
              onPush={() => mutate(() => api.streams.push(stream.id))}
              onCancel={() => mutate(() => api.streams.cancel(stream.id))}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
