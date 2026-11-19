import { useEffect, useState } from "react";
import { api } from "../api";
import type { CatalogItem } from "../types";

type Props = {
  disabled?: boolean;
  onAdd: (offerId: number) => Promise<void>;
};

export function OfferSearch({ disabled, onAdd }: Props) {
  const [query, setQuery] = useState("");
  const [offers, setOffers] = useState<CatalogItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      api.catalogs
        .offers(query)
        .then((items) => setOffers(items.slice(0, 50)))
        .catch(() => setOffers([]));
    }, 200);
    return () => window.clearTimeout(handle);
  }, [query]);

  async function handleAdd() {
    if (selectedId === "") {
      return;
    }
    setBusy(true);
    try {
      await onAdd(Number(selectedId));
      setSelectedId("");
      setQuery("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="offer-search">
      <input
        placeholder="Поиск оффера"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        disabled={disabled}
      />
      <select
        value={selectedId}
        onChange={(event) => setSelectedId(event.target.value ? Number(event.target.value) : "")}
        disabled={disabled}
      >
        <option value="">Оффер</option>
        {offers.map((offer) => (
          <option key={offer.id} value={offer.id}>
            #{offer.id} · {offer.name}
          </option>
        ))}
      </select>
      <button className="btn primary" type="button" disabled={disabled || busy || selectedId === ""} onClick={handleAdd}>
        {busy ? "Добавление…" : "Добавить"}
      </button>
    </div>
  );
}
