import { OfferRow } from "./OfferRow";
import { OfferSearch } from "./OfferSearch";
import type { Stream } from "../types";

type Props = {
  stream: Stream;
  busy?: boolean;
  onAdd: (offerId: number) => Promise<void>;
  onRemove: (offerId: number) => Promise<void>;
  onRestore: (offerId: number) => Promise<void>;
  onPin: (offerId: number, pinned: boolean) => Promise<void>;
  onPush: () => Promise<void>;
  onCancel: () => Promise<void>;
};

export function StreamCard({ stream, busy, onAdd, onRemove, onRestore, onPin, onPush, onCancel }: Props) {
  return (
    <article className={`card stream-card ${stream.is_dirty ? "is-dirty" : ""}`}>
      <header className="stream-head">
        <div>
          <h3>{stream.name}</h3>
          {stream.is_dirty ? <p className="muted">Не опубликовано</p> : null}
        </div>
        <div className="stream-actions">
          <button className="btn" type="button" disabled={busy || !stream.is_dirty} onClick={onCancel}>
            Отмена
          </button>
          <button className="btn primary" type="button" disabled={busy || !stream.is_dirty} onClick={onPush}>
            Опубликовать
          </button>
        </div>
      </header>

      {stream.offers.length > 0 ? (
        <div className="offer-list">
          {stream.offers.map((offer) => (
            <OfferRow
              key={offer.keitaro_offer_id}
              offer={offer}
              busy={busy}
              onRemove={() => onRemove(offer.keitaro_offer_id)}
              onRestore={() => onRestore(offer.keitaro_offer_id)}
              onPin={(pinned) => onPin(offer.keitaro_offer_id, pinned)}
            />
          ))}
        </div>
      ) : null}

      <OfferSearch disabled={busy} onAdd={onAdd} />
    </article>
  );
}
