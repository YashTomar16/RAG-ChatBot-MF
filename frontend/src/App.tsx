import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { BootstrapProvider } from "./context/BootstrapContext";
import { AppLayout } from "./layout/AppLayout";
import { ChatPage } from "./pages/ChatPage";
import { ComparePage } from "./pages/ComparePage";
import { DiscoverPage, FundDetailPage } from "./pages/DiscoverPage";
import { HomePage, LearnPage, PortfolioPage } from "./pages/HomePortfolioLearn";

export default function App() {
  return (
    <BrowserRouter>
      <BootstrapProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<HomePage />} />
            <Route path="discover" element={<DiscoverPage />} />
            <Route path="funds/:id" element={<FundDetailPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="portfolio" element={<PortfolioPage />} />
            <Route path="learn" element={<LearnPage />} />
            <Route path="compare" element={<ComparePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BootstrapProvider>
    </BrowserRouter>
  );
}
