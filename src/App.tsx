import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import { Routes, Route, Link } from "react-router-dom";
import Metrics from "./pages/Metrics";
import Logging from "./pages/Logging";

export default function App() {
  const queryClient = new QueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />

        <div style={{ padding: 12 }}>
          <nav style={{ padding: 16, borderBottom: "1px solid #eee" }}>
            <Link to="/metrics" style={{ marginRight: 16 }}>View Metrics</Link>
            <Link to="/logging">View Logging</Link>
          </nav>
        </div>

        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/logging" element={<Logging />} />
          {/* Keep custom routes above the catch-all */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </TooltipProvider>
    </QueryClientProvider>
  );
}
