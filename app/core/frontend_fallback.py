import json


def build_mobile_web_demo_fallback(task: str, reason: str) -> dict:
    package_json = {
        "name": "mobile-web-demo-fallback",
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
            "start": "vite preview --host 0.0.0.0 --port ${PORT:-4173}",
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.0.3",
            "vite": "^4.4.9",
        },
    }

    app_jsx = r'''import React, { useMemo, useState } from "react";
import "./index.css";

const stays = [
  { id: 1, title: "Harbor Nest", city: "Baku", type: "Apartment", price: 84, rating: 4.8, tag: "Sea view" },
  { id: 2, title: "Old Town Loft", city: "Baku", type: "Loft", price: 72, rating: 4.7, tag: "Walkable" },
  { id: 3, title: "Garden Studio", city: "Gabala", type: "Cabin", price: 96, rating: 4.9, tag: "Quiet" },
];

export default function App() {
  const [screen, setScreen] = useState("discover");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(stays[0]);
  const [guests, setGuests] = useState(2);
  const [confirmed, setConfirmed] = useState(false);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return stays;
    return stays.filter((stay) => `${stay.title} ${stay.city} ${stay.type}`.toLowerCase().includes(q));
  }, [query]);

  const openDetails = (stay) => {
    setSelected(stay);
    setConfirmed(false);
    setScreen("details");
  };

  const total = selected.price * Math.max(1, guests);

  return (
    <div className="shell">
      <div className="phone">
        <header className="topbar">
          <div>
            <span className="eyebrow">StayFlow demo</span>
            <h1>{screen === "discover" ? "Find a stay" : selected.title}</h1>
          </div>
          {screen !== "discover" && <button className="ghost" onClick={() => setScreen("discover")}>Back</button>}
        </header>

        {screen === "discover" && (
          <main className="content">
            <label className="search">
              <span>Destination</span>
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search city or stay" />
            </label>

            <section className="quick">
              <button onClick={() => setQuery("Baku")}>Baku</button>
              <button onClick={() => setQuery("Gabala")}>Nature</button>
              <button onClick={() => setQuery("")}>All</button>
            </section>

            <section className="list">
              {filtered.map((stay) => (
                <button key={stay.id} className="card" onClick={() => openDetails(stay)}>
                  <span className="photo">{stay.city.slice(0, 2).toUpperCase()}</span>
                  <span className="cardText">
                    <strong>{stay.title}</strong>
                    <small>{stay.city} · {stay.type} · {stay.tag}</small>
                    <b>${stay.price}/night · {stay.rating}</b>
                  </span>
                </button>
              ))}
              {filtered.length === 0 && <p className="empty">No stays match this search.</p>}
            </section>
          </main>
        )}

        {screen === "details" && (
          <main className="content">
            <div className="hero">{selected.tag}</div>
            <div className="details">
              <h2>{selected.title}</h2>
              <p>{selected.city} · {selected.type} · guest favorite rating {selected.rating}</p>
              <p>A compact booking-style flow with mock availability, local state, and no backend dependency.</p>
            </div>
            <button className="primary" onClick={() => setScreen("book")}>Reserve demo stay</button>
          </main>
        )}

        {screen === "book" && (
          <main className="content">
            <section className="summary">
              <strong>{selected.title}</strong>
              <span>${selected.price}/night</span>
            </section>
            <label className="field">
              Guests
              <input type="number" min="1" max="6" value={guests} onChange={(event) => setGuests(Number(event.target.value))} />
            </label>
            <section className="summary total">
              <span>Total demo price</span>
              <strong>${total}</strong>
            </section>
            {confirmed ? (
              <div className="success">
                <strong>Demo booking confirmed</strong>
                <span>Your clickable prototype flow is working.</span>
              </div>
            ) : (
              <button className="primary" onClick={() => setConfirmed(true)}>Confirm demo booking</button>
            )}
          </main>
        )}

        <nav className="tabs">
          <button className={screen === "discover" ? "active" : ""} onClick={() => setScreen("discover")}>Explore</button>
          <button className={screen === "details" ? "active" : ""} onClick={() => setScreen("details")}>Details</button>
          <button className={screen === "book" ? "active" : ""} onClick={() => setScreen("book")}>Book</button>
        </nav>
      </div>
    </div>
  );
}
'''

    css = r'''* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #eef2f6;
  color: #17202a;
}
button, input { font: inherit; }
.shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}
.phone {
  width: min(430px, 100%);
  min-height: 760px;
  background: #fbfcfd;
  border: 1px solid #d9e0e8;
  border-radius: 28px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(18, 31, 49, 0.16);
}
.topbar {
  padding: 22px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5eaf0;
}
.eyebrow {
  display: block;
  font-size: 12px;
  color: #607086;
  margin-bottom: 4px;
}
h1, h2, p { margin: 0; }
h1 { font-size: 28px; }
h2 { font-size: 24px; }
.ghost {
  border: 0;
  background: #eef3f8;
  border-radius: 999px;
  padding: 8px 12px;
}
.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
.search, .field {
  display: grid;
  gap: 8px;
  color: #566579;
  font-size: 13px;
}
input {
  width: 100%;
  border: 1px solid #d9e0e8;
  border-radius: 14px;
  padding: 14px;
  background: #fff;
}
.quick {
  display: flex;
  gap: 10px;
  margin: 16px 0;
}
.quick button {
  border: 0;
  background: #17202a;
  color: white;
  border-radius: 999px;
  padding: 10px 14px;
}
.list { display: grid; gap: 12px; }
.card {
  display: flex;
  gap: 14px;
  align-items: center;
  width: 100%;
  text-align: left;
  border: 1px solid #e2e8ef;
  background: #fff;
  border-radius: 18px;
  padding: 12px;
}
.photo {
  width: 76px;
  height: 76px;
  border-radius: 16px;
  background: linear-gradient(135deg, #47b2a0, #285c8f);
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
}
.cardText {
  min-width: 0;
  display: grid;
  gap: 5px;
}
.cardText small { color: #66758a; }
.cardText b { color: #1d6b61; }
.hero {
  min-height: 220px;
  border-radius: 24px;
  background: linear-gradient(135deg, #285c8f, #47b2a0 55%, #f0c35b);
  color: white;
  display: grid;
  place-items: end start;
  padding: 22px;
  font-size: 24px;
  font-weight: 800;
}
.details {
  display: grid;
  gap: 12px;
  margin: 20px 0;
  line-height: 1.5;
}
.primary {
  width: 100%;
  border: 0;
  border-radius: 16px;
  padding: 15px;
  background: #1f6feb;
  color: white;
  font-weight: 800;
}
.summary {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e2e8ef;
  border-radius: 18px;
  margin-bottom: 16px;
}
.total { align-items: center; }
.success {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: #e9f8f1;
  color: #176348;
}
.empty { color: #66758a; padding: 20px 0; }
.tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #e5eaf0;
  background: #fff;
}
.tabs button {
  border: 0;
  border-radius: 14px;
  padding: 12px 8px;
  background: transparent;
  color: #607086;
}
.tabs button.active {
  background: #e8f1ff;
  color: #1f5fbf;
  font-weight: 800;
}
@media (max-width: 520px) {
  .shell { padding: 0; }
  .phone {
    width: 100%;
    min-height: 100vh;
    border-radius: 0;
    border: 0;
  }
}
'''

    return {
        "role": "senior_frontend_fallback",
        "deliverables": {
            "frontend_summary": {
                "implementation_scope": ["Clickable mobile-style accommodation booking demo"],
                "implemented_screens_or_components": ["Explore", "Details", "Booking confirmation"],
                "api_integration_points": ["None; local mock data only"],
            },
            "ui_behavior_notes": {
                "validation_behavior": ["Guest count is constrained by numeric input"],
                "loading_and_error_states": ["Empty search state and success confirmation are included"],
                "interaction_notes": ["Tabs, search chips, cards, details, and booking confirmation are clickable"],
            },
        },
        "files": [
            {"path": "package.json", "content": json.dumps(package_json, indent=2)},
            {
                "path": "index.html",
                "content": '<!doctype html>\n<html lang="en">\n<head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>Mobile Web Demo</title></head>\n<body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body>\n</html>\n',
            },
            {
                "path": "vite.config.js",
                "content": 'import { defineConfig } from "vite";\nimport react from "@vitejs/plugin-react";\n\nexport default defineConfig({\n  plugins: [react()],\n});\n',
            },
            {
                "path": "src/main.jsx",
                "content": 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App.jsx";\n\nReactDOM.createRoot(document.getElementById("root")).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);\n',
            },
            {"path": "src/App.jsx", "content": app_jsx},
            {"path": "src/index.css", "content": css},
        ],
        "decisions": ["Used deterministic fallback because generated frontend did not pass validation"],
        "assumptions": ["The user needs a clickable browser demo before native mobile packaging"],
        "open_questions": [],
        "fallback_used": True,
        "fallback_reason": reason,
        "source_task": task,
        "contract_ok": True,
        "contract_errors": [],
    }
