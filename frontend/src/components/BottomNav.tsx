import { NavLink } from "react-router-dom";
import type { TabId } from "../types";

const TABS: Array<{ id: TabId; label: string; path: string }> = [
  { id: "home", label: "Home", path: "/" },
  { id: "discover", label: "Discover", path: "/discover" },
  { id: "chat", label: "Chat", path: "/chat" },
  { id: "portfolio", label: "Portfolio", path: "/portfolio" },
  { id: "learn", label: "Learn", path: "/learn" },
];

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Main navigation">
      <div className="bottom-nav-inner">
        {TABS.map((tab) => (
          <NavLink
            key={tab.id}
            to={tab.path}
            className={({ isActive }) => `nav-btn${isActive ? " active" : ""}`}
            end={tab.path === "/"}
          >
            {tab.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
