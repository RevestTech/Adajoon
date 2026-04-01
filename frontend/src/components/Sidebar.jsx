import { useState } from "react";

export default function Sidebar({
  categories,
  countries,
  activeCategory,
  activeCountry,
  onSelectCategory,
  onSelectCountry,
}) {
  const [tab, setTab] = useState("categories");

  return (
    <aside className="sidebar">
      <div style={{ display: "flex", gap: "4px", padding: "0 12px", marginBottom: "16px" }}>
        <TabButton active={tab === "categories"} onClick={() => setTab("categories")}>
          Categories
        </TabButton>
        <TabButton active={tab === "countries"} onClick={() => setTab("countries")}>
          Countries
        </TabButton>
      </div>

      {tab === "categories" && (
        <div className="sidebar-section">
          <div className="sidebar-title">Categories</div>
          <div
            className={`sidebar-item ${!activeCategory ? "active" : ""}`}
            onClick={() => onSelectCategory(null)}
          >
            <span>All Categories</span>
          </div>
          {categories.map((cat) => (
            <div
              key={cat.id}
              className={`sidebar-item ${activeCategory === cat.id ? "active" : ""}`}
              onClick={() => onSelectCategory(cat.id)}
            >
              <span>{cat.name}</span>
              <span className="sidebar-count">{cat.channel_count}</span>
            </div>
          ))}
        </div>
      )}

      {tab === "countries" && (
        <div className="sidebar-section">
          <div className="sidebar-title">Countries</div>
          <div
            className={`sidebar-item ${!activeCountry ? "active" : ""}`}
            onClick={() => onSelectCountry(null)}
          >
            <span>All Countries</span>
          </div>
          {countries.slice(0, 80).map((c) => (
            <div
              key={c.code}
              className={`sidebar-item ${activeCountry === c.code ? "active" : ""}`}
              onClick={() => onSelectCountry(c.code)}
            >
              <span>
                {c.flag && <span className="country-flag">{c.flag}</span>}
                {c.name}
              </span>
              <span className="sidebar-count">{c.channel_count}</span>
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1,
        padding: "8px 12px",
        background: active ? "rgba(233,69,96,0.15)" : "transparent",
        border: "1px solid " + (active ? "var(--accent)" : "var(--border)"),
        borderRadius: "var(--radius-sm)",
        color: active ? "var(--accent)" : "var(--text-secondary)",
        cursor: "pointer",
        fontSize: "12px",
        fontWeight: 600,
        fontFamily: "inherit",
        transition: "all 0.15s",
      }}
    >
      {children}
    </button>
  );
}
