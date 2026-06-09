import { BootstrapProvider } from "./context/BootstrapContext";
import { ChatPage } from "./pages/ChatPage";

export default function App() {
  return (
    <BootstrapProvider>
      <ChatPage />
    </BootstrapProvider>
  );
}
