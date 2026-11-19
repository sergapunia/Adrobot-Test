import type { StreamOffer } from "../types";

type Props = {
  offer: StreamOffer;
  busy?: boolean;
  onRemove: () => void;
  onRestore: () => void;
  onPin: (pinned: boolean) => void;
};

export function OfferRow({ offer, busy, onRemove, onRestore, onPin }: Props) {
  const removed = offer.status === "removed";

  return (
    <div className={`offer-row ${removed ? "is-removed" : ""}`}>
      <div>
        <div className="offer-name">{offer.name}</div>
        <div className="muted">ID {offer.keitaro_offer_id}</div>
      </div>
      <div className={`share ${removed ? "zero" : ""}`}>
        {offer.share}%{offer.is_pinned ? " · пин" : ""}
      </div>
      <div className="offer-actions">
        {removed ? (
          <button className="btn ghost" type="button" disabled={busy} onClick={onRestore}>
            Вернуть
          </button>
        ) : (
          <>
            <button className="btn ghost" type="button" disabled={busy} onClick={() => onPin(!offer.is_pinned)}>
              {offer.is_pinned ? "Открепить" : "Закрепить"}
            </button>
            <button className="btn danger" type="button" disabled={busy} onClick={onRemove}>
              Удалить
            </button>
          </>
        )}
      </div>
    </div>
  );
}
