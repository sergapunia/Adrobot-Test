import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { ComboField } from "../components/ComboField";
import { COUNTRIES } from "../countries";
import type { Campaign, CatalogItem } from "../types";

export function CreateCampaign() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [country, setCountry] = useState("");
  const [offerId, setOfferId] = useState<number | "">("");
  const [domainId, setDomainId] = useState<number | "">("");
  const [groupId, setGroupId] = useState<number | "">("");
  const [sourceId, setSourceId] = useState<number | "">("");
  const [domains, setDomains] = useState<CatalogItem[]>([]);
  const [groups, setGroups] = useState<CatalogItem[]>([]);
  const [sources, setSources] = useState<CatalogItem[]>([]);
  const [offers, setOffers] = useState<CatalogItem[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [geos, setGeos] = useState(COUNTRIES);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([
      api.catalogs.domains(),
      api.catalogs.groups(),
      api.catalogs.trafficSources(),
      api.catalogs.offers(),
      api.campaigns.list(),
    ])
      .then(([domainRows, groupRows, sourceRows, offerRows, campaignRows]) => {
        setDomains(domainRows);
        setGroups(groupRows);
        setSources(sourceRows);
        setOffers(offerRows);
        setCampaigns(campaignRows);
        if (domainRows[0]) setDomainId(domainRows[0].id);
        if (sourceRows[0]) setSourceId(sourceRows[0].id);
        if (offerRows[0]) setOfferId(offerRows[0].id);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!name.trim() || !country || !offerId || domainId === "" || sourceId === "") {
      setError("Заполните название, гео, оффер, домен и источник.");
      return;
    }
    setBusy(true);
    try {
      const campaign = await api.campaigns.create({
        name: name.trim(),
        country_code: country,
        offer_id: Number(offerId),
        domain_id: Number(domainId),
        group_id: groupId === "" ? null : Number(groupId),
        traffic_source_id: Number(sourceId),
      });
      navigate(`/campaigns/${campaign.keitaro_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось создать кампанию");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <form className="card form" onSubmit={onSubmit}>
        <h1>Новая кампания</h1>
        {error ? <p className="error banner">{error}</p> : null}
        <label>
          Название
          <div className="prefix-field">
            <span className="prefix-chip">test_ukolov_</span>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="campaign1" />
          </div>
        </label>
        <div className="grid-2">
          <label>
            Гео
            <ComboField
              options={geos}
              value={country}
              onChange={setCountry}
              placeholder="Выберите или введите код"
              createHint="Добавить"
              onCreate={async (text) => {
                const code = text.trim().toUpperCase().replace(/[^A-Z]/g, "").slice(0, 2);
                if (code.length !== 2) {
                  throw new Error("Код страны — две буквы, например DE");
                }
                setGeos((current) => (current.some((item) => item.id === code) ? current : [...current, { id: code, label: code }]));
                return code;
              }}
            />
          </label>
          <label>
            Оффер
            <ComboField
              options={offers.map((item) => ({ id: String(item.id), label: `#${item.id} · ${item.name}` }))}
              value={offerId === "" ? "" : String(offerId)}
              onChange={(id) => setOfferId(id ? Number(id) : "")}
              placeholder="Выберите оффер"
              createHint="ID"
              onCreate={async (text) => {
                const id = Number(text.replace(/\D/g, ""));
                if (!id) {
                  throw new Error("Укажите ID оффера");
                }
                if (!offers.some((item) => item.id === id)) {
                  setOffers((current) => [...current, { id, name: `Offer #${id}` }]);
                }
                return String(id);
              }}
            />
          </label>
        </div>
        <label>
          Домен
          <ComboField
            options={domains.map((item) => ({ id: String(item.id), label: item.name }))}
            value={domainId === "" ? "" : String(domainId)}
            onChange={(id) => setDomainId(id ? Number(id) : "")}
            placeholder="Выберите или введите"
            onCreate={async (name) => {
              const created = await api.catalogs.createDomain(name);
              setDomains((current) => [...current, created]);
              return String(created.id);
            }}
          />
        </label>
        <label>
          Группа
          <ComboField
            options={groups.map((item) => ({ id: String(item.id), label: item.name }))}
            value={groupId === "" ? "" : String(groupId)}
            onChange={(id) => setGroupId(id ? Number(id) : "")}
            placeholder="Выберите или введите"
            onCreate={async (name) => {
              const created = await api.catalogs.createGroup(name);
              setGroups((current) => [...current, created]);
              return String(created.id);
            }}
          />
        </label>
        <label>
          Источник
          <ComboField
            options={sources.map((item) => ({ id: String(item.id), label: item.name }))}
            value={sourceId === "" ? "" : String(sourceId)}
            onChange={(id) => setSourceId(id ? Number(id) : "")}
            placeholder="Выберите или введите"
            onCreate={async (name) => {
              const created = await api.catalogs.createTrafficSource(name);
              setSources((current) => [...current, created]);
              return String(created.id);
            }}
          />
        </label>
        <button className="btn primary lg" type="submit" disabled={busy}>
          {busy ? "Создание…" : "Создать"}
        </button>
      </form>

      {campaigns.length > 0 ? (
        <section className="card">
          <h2>Кампании</h2>
          <ul className="campaign-list">
            {campaigns.map((campaign) => (
              <li key={campaign.keitaro_id}>
                <Link to={`/campaigns/${campaign.keitaro_id}`}>
                  {campaign.name}
                  <span className="muted">#{campaign.keitaro_id}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
