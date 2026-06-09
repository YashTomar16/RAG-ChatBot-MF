import { Outlet } from "react-router-dom";
import { BottomNav } from "../components/BottomNav";
import { DisclaimerBanner } from "../components/DisclaimerBanner";
import { useTheme } from "../hooks/useTheme";

export function AppLayout() {
  const { dark, toggle } = useTheme();

  return (
    <div className="app-shell" data-theme={dark ? "dark" : "light"}>
      <div className="app-topbar">
        <span className="app-topbar-caption">HDFC · Groww corpus</span>
        <button type="button" className="theme-toggle" onClick={toggle} aria-label="Toggle dark mode">
          {dark ? "Light" : "Dark"}
        </button>
      </div>
      <DisclaimerBanner />
      <Outlet />
      <BottomNav />
    </div>
  );
}
