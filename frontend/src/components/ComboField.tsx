import { useEffect, useMemo, useRef, useState } from "react";

export type ComboOption = { id: string; label: string };

type Props = {
  options: ComboOption[];
  value: string;
  onChange: (id: string) => void;
  onCreate?: (text: string) => Promise<string>;
  placeholder?: string;
  createHint?: string;
};

export function ComboField({ options, value, onChange, onCreate, placeholder, createHint }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const selected = options.find((option) => option.id === value);
  const [query, setQuery] = useState(selected?.label ?? "");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      setQuery(selected?.label ?? "");
    }
  }, [selected?.label, open]);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return options.slice(0, 40);
    }
    return options.filter((option) => option.label.toLowerCase().includes(needle) || option.id.toLowerCase().includes(needle)).slice(0, 40);
  }, [options, query]);

  const exact = options.some(
    (option) => option.label.toLowerCase() === query.trim().toLowerCase() || option.id.toLowerCase() === query.trim().toLowerCase(),
  );
  const canCreate = Boolean(onCreate && query.trim() && !exact);

  async function create() {
    if (!onCreate || !query.trim()) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const id = await onCreate(query.trim());
      onChange(id);
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось создать");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="combo" ref={rootRef}>
      <input
        value={query}
        placeholder={placeholder}
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          if (!event.target.value.trim()) {
            onChange("");
          }
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            if (filtered[0] && !canCreate) {
              onChange(filtered[0].id);
              setQuery(filtered[0].label);
              setOpen(false);
            } else if (canCreate) {
              void create();
            }
          }
        }}
      />
      {open ? (
        <div className="combo-menu">
          {filtered.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`combo-option ${option.id === value ? "is-active" : ""}`}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => {
                onChange(option.id);
                setQuery(option.label);
                setOpen(false);
              }}
            >
              {option.label}
            </button>
          ))}
          {canCreate ? (
            <button
              type="button"
              className="combo-option create"
              disabled={busy}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => void create()}
            >
              {busy ? "Создание…" : `${createHint ?? "Создать"} «${query.trim()}»`}
            </button>
          ) : null}
          {filtered.length === 0 && !canCreate ? <div className="combo-empty">Ничего не найдено</div> : null}
          {error ? <div className="combo-empty">{error}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
