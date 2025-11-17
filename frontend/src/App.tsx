import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/components/theme-provider";
import AdminPanelLayout from "@/components/admin-panel/admin-panel-layout";
import { MonitorPanel } from "@/components/monitor/MonitorPanel";
import { Dashboard } from "@/pages/Dashboard";
import { TestCardPage } from "@/pages/TestCardPage";

function App() {
    return (
        <ThemeProvider defaultTheme="system" storageKey="minecompanion-theme">
            <BrowserRouter>
                <AdminPanelLayout>
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/test-card" element={<TestCardPage />} />
                        <Route path="/monitor" element={<MonitorPanel />} />
                    </Routes>
                </AdminPanelLayout>
            </BrowserRouter>
        </ThemeProvider>
    );
}

export default App;
